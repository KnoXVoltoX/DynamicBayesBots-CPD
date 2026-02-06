#include <MyKilobot.h>

#include <iomanip>
#include <sstream>
#include "ProgressBar.hpp"

#include <kilosim/ConfigParser.h>
#include <kilosim/Kilobot.h>
#include <kilosim/Logger.h>
#include <kilosim/Random.h>
#include <kilosim/Timer.h>
#include <kilosim/Viewer.h>


// Aggregator to collect certain data of the trials:
std::vector<double> believed_ratio(std::vector<Kilosim::Robot *> &robots)
{
    // Get the mean believed pattern ratio of all robots
    std::vector<double> ratio(1, 0.0);

    float ratio_belief = 0.0;
    for (auto &robot : robots)
    {
        // Downcast to get access to believed ratio of the robots
        Kilosim::MyKilobot *kb = (Kilosim::MyKilobot *)robot;
        ratio_belief += kb->log_q;

    }
    ratio[0] = (double)ratio_belief / robots.size();

    return ratio;
}


std::vector<double> get_decision(std::vector<Kilosim::Robot *> &robots)
{
    // Get the decisions of the robots
    std::vector<double> decision(3);
    int undecided = 0;
    int count_w = 0;
    int count_b = 0;
    for (auto &robot : robots)
    {
        // Get access to decisions of the robot
        Kilosim::MyKilobot *kb = (Kilosim::MyKilobot *)robot;
        if(kb->log_df==1){
            count_w++;
        }
        else if(kb->log_df==0){
            count_b++;
        }
        else{
            undecided++;
        }
    }
    decision[0] = undecided;
    decision[1] = count_w;
    decision[2] = count_b;

    return decision;
}


std::vector<double> robot_decisions(std::vector<Kilosim::Robot *> &robots)
{
    // Get each individual robot's belief
    std::vector<double> decisions(robots.size());
    for (int i = 0; i < robots.size(); i++)
    {
        Kilosim::MyKilobot *kb = (Kilosim::MyKilobot *)robots[i];
        decisions[i] = kb->log_q;
    }
    return decisions;
}


std::vector<double> robot_resets(std::vector<Kilosim::Robot *> &robots)
{
    // Get each individual robot's decision
    std::vector<double> resets(robots.size());
    for (int i = 0; i < robots.size(); i++)
    {
        Kilosim::MyKilobot *kb = (Kilosim::MyKilobot *)robots[i];
        resets[i] = kb->log_res;
    }
    return resets;
}


// ConfigParser taken from Julia Ebert's code
nlohmann::json get_val(Kilosim::ConfigParser config, std::string key,
                       std::string compare_param, int compare_ind)
{
    // Hacky approach to getting the indexed value if this is the compare_param,
    // or otherwise just returning the scalar value
    if (compare_param == key)
    {
        return config.get(key)[compare_ind];
    }
    else
    {
        return config.get(key);
    }
}


int main(int argc, char *argv[])
{
    Timer timer_overall;
    Timer timer_step;
    timer_overall.start();

    // Get config file name
    std::vector<std::string> args(argv, argv + argc);
    if (args.size() < 2)
    {
        std::cout << "ERROR: You must provide a config file name" << std::endl;
        exit(1);
    }


    // Getting the parameters of the config.json
    Kilosim::ConfigParser config(args[1]);
    uint start_trial = config.get("start_trial");
    double trial_duration = config.get("trial_duration");                                         // Absolute time of the run in seconds (simulator is about 7 times faster than real time)
    const std::string log_dir = config.get("log_dir");
    seed_rand(config.get("seed"));
    const bool posFeedback = true;
    const int progress_update_freq = 10;
    const int limit = trial_duration / progress_update_freq;

    // Parameters that may be automatically changed within the config.json
    const std::string compare_param = config.get("compare_param");
    nlohmann::json compare_vals = config.get(compare_param);
    const uint num_compare_vals = compare_vals.size();

    for (uint compare_ind = 0; compare_ind < num_compare_vals; compare_ind++)
    {
        uint num_trials = get_val(config,"num_trials", compare_param, compare_ind);
        int num_envs = get_val(config,"num_environments", compare_param, compare_ind);             // Number of used environments (up to 5 different ones atm. Directory of the environment png/ jpg has to be in the config.json)
        num_envs-=1;
        int tChange = get_val(config,"environmentChange", compare_param, compare_ind);             // Time interval after which the environment is changed
        uint tau = get_val(config,"tau", compare_param, compare_ind);                              // Observation interval (1 observation every x seconds)
        uint log_freq = get_val(config, "log_freq", compare_param, compare_ind);
        double credThresh = get_val(config, "credibleThreshold", compare_param, compare_ind);      // Threshold that has to be reached to make a decision
        float resetThresh = get_val(config, "resetThreshold", compare_param, compare_ind);         // If after a already made decision the belive decreases below that threshold the robot reset itself.
        float sampleLim = get_val(config, "sampleLimit", compare_param, compare_ind);              // The robot does not collect any more proofs for the winning observation, once the limit is reached. It immeadiatly starts collecting again as soons as it is below this limit.

        json compare_val = config.get(compare_param)[compare_ind];
        std::ostringstream cs;
        cs << compare_val;
        std::string compare_val_str = cs.str();
        std::string trial_dur = std::to_string(int(trial_duration));
        std::string cred_thresh = std::to_string(int(credThresh*100));
        std::string log_filename = log_dir + "log_" + trial_dur + "s_" +"pc=0."+cred_thresh+"_"+ compare_param + '=' + compare_val_str + ".h5";


        for (uint trial = start_trial; trial < (num_trials + start_trial); trial++)
        {
            // Progressbar
            printf("\n\n");
            printf("-------------------------------------------------------\n");
            std::cout << "    TRIAL " << trial << " " << compare_param << " = " << compare_val << std::endl;
            printf("-------------------------------------------------------\n");
            ProgressBar progress_bar(limit, 50);

            // Create world
            Kilosim::World world(
                config.get("world_width"),
                config.get("world_height"),
                config.get("light_pattern_filename"),
                config.get("num_threads"));

            // Counter initialized with 1 to know in which environment we are
            int env_counter = 1;

            // Creates a grid of 10x10 uniform distributed robots
            int num_rows = 10;
            int num_robots = config.get("num_robots");
            std::vector<Kilosim::Robot *> robots;
            robots.resize(num_robots);
            // Create robot(s)
            for (int n = 0; n < num_robots; n++)
            {
                robots[n] = new Kilosim::MyKilobot();
                world.add_robot(robots[n]);
                robots[n]->robot_init(floor(n / num_rows) * 240 + 120, (n % num_rows) * 240 + 120, PI * n / 2);
            }
            int k = 0;
            for (auto &robot : robots)
            {
                // Downcast to initialize the public custom variables of each robot
                Kilosim::MyKilobot *kb = (Kilosim::MyKilobot *)robot;
                kb->id = k;
                kb->uPos = posFeedback;
                kb->pc = credThresh;
                kb->pres = resetThresh;
                kb->plim = sampleLim;
                k += 1;
            }
            world.check_validity();

            // Create logger
            Kilosim::Logger logger(
                world,
                log_filename,
                trial,
                true);
            // Add the aggregators from above
            logger.add_aggregator("mean_believed_ratio", believed_ratio);
            logger.add_aggregator("mean_robot_decision", get_decision);
            logger.add_aggregator("robots_decision", robot_decisions);
            logger.add_aggregator("robots_reset", robot_resets);
            logger.log_config(config);

            // Create Viewer to visualize the world
            Kilosim::Viewer viewer(world, 800);
            int step_count = 0;

            // Actual trial procedure
            while (world.get_time() < trial_duration)
            {
                // Interval for the progressbar update
                if (world.get_tick() % (progress_update_freq * world.get_tick_rate()) == 0)
                {
                    ++progress_bar;
                    progress_bar.display();
                }

                // Run a simulation step
                // This automatically increments the tick
                step_count++;
                timer_step.start();
                world.step();
                timer_step.stop();

                // Draw the world
                viewer.draw();

                // Setting the flag for the observational interval
                if ((world.get_tick() % (tau * world.get_tick_rate())) == 0)
                {
                    k = 1;
                    for (auto &robot : robots)
                    {
                        Kilosim::MyKilobot *kb = (Kilosim::MyKilobot *)robot;
                        kb->observe = true;

                        // Print the check variable of the first robot
                        // if(k==1){
                        //     Kilosim::MyKilobot *qb = (Kilosim::MyKilobot *)robot;
                        //     printf("Robot=  %f\n\n", qb->check);
                        //     k = 0;
                        // }
                    }

                }

                // Log the current state of the world every X seconds
                if ((world.get_tick() % (log_freq * world.get_tick_rate())) == 0)
                {
                    logger.log_state();
                }

                // Set new lightpattern to change environment (add more cases to increase the number of environments, but change it also in the config.json)
                if ((world.get_tick() % (tChange * world.get_tick_rate())) == 0)
                {
                        switch(env_counter) {
                            case 1:
                              world.set_light_pattern(config.get("light_pattern_filename1"));
                              if(env_counter<num_envs){env_counter++;}
                              break;
                            case 2:
                              world.set_light_pattern(config.get("light_pattern_filename2"));
                              if(env_counter<num_envs){env_counter++;}
                              break;
                            case 3:
                              world.set_light_pattern(config.get("light_pattern_filename3"));
                              if(env_counter<num_envs){env_counter++;}
                              break;
                            case 4:
                              world.set_light_pattern(config.get("light_pattern_filename4"));
                              if(env_counter<num_envs){env_counter++;}
                              break;
                        }
                    viewer.m_bg_texture.loadFromImage(world.get_light_pattern());
                }


            }
            progress_bar.done();
            world.printTimes();
            for (int n = 0; n < num_robots; n++)
                delete robots[n];

            printf("Completed trial %d\n\n", trial);
            std::cerr << "m Steps taken = " << step_count << std::endl;
        }
    }

    printf("Simulations successfully completed\n\n");

    std::cerr << "t Step    = " << timer_step.accumulated() << " s" << std::endl;
    std::cerr << "t Overall = " << timer_overall.stop() << " s" << std::endl;
    return 0;
}
