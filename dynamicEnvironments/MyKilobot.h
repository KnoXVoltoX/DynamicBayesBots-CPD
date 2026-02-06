#include <kilosim/Kilobot.h>

#include <boost/math/distributions/beta.hpp>
#include <boost/math/special_functions/beta.hpp>
#include <boost/math/distributions/exponential.hpp>
#include <iostream>
#include <cmath>
#include <vector>
#include <random>
#include <stdio.h>
// #include <conio.h>
#include <python3.8/Python.h>
// #include "pyhelper.hpp"
#include "numpy/arrayobject.h"
// #define PY_SSIZE_T_CLEAN



namespace Kilosim
{

class MyKilobot : public Kilobot
{
  public:
    // These parameters are accessible from the main.cpp
    int16_t light_intensity = -1;
    bool observe = false;
    bool endPy = false;
    int id = 0;                       // ID of the robot
    bool uPos = true;                 // Postive feedback (atm always true)
    float pc = 0.0;                   // Credible threshold (min. propab. mass)
    float pres = 0.0;                 // Reset threshold
    float plim = 0.0;                 // Sample limit
    float log_q = 0.0;
    int log_df = 0;
    int log_res = 0;
    int log_C = -1;
    float log_noCPD = 0;
    float check = 1.0;                // Debug/ Monitoring variable


  private:
    #define STOP 0
    #define FORWARD 1
    #define LEFT 2
    #define RIGHT 3

    // Initialize
    message_t transmit_msg;
    bool new_message = 0;
    uint32_t last_checked = 0;
    int random_number = 0;
    int rw = 0;                       // Random walk (1: straigth segment, 0: turn)
    int curr_motion = 0;              // Current motion of the random walk
    uint32_t next_check_dur;
    double alpha0 = 10.0;             // Prior parameter (initialization of beta distribution)
    double alpha;
    double beta;
    float q = 0.5;                    // Beta CDF
    int16_t C;                        // Color observation
    uint32_t i = 0;                   // Observation index
    int m[9];                         // Message array
    std::vector<int> s;               // Dictionary of received observations
    std::vector<int> s_reset;            // Dictionary of received resets
    std::vector<int> s_decided;
    std::vector<int> probes;
    std::vector<int> cp;
    int df = -1;                      // Decision
    int dReset = 0;                   // Reset flag
    int countR = 0;                   // Counter of resets
    double lambda = 1/(240*SECOND);   // SECOND to get kiloticks per second
    int turn_max = 12*SECOND;         // 12 --> 2*PI/0.5 for a whole turn with a turnspeed of 0.5rad/s
    int lock_dict = 0;
    int pyini = 0;
    int looprun = 0;
    int probeC = 0;
    uint32_t last_res = 0;
    uint32_t res_dur = 50*SECOND;
    int msgReset = 0;
    int receiveReset = 0;
    int neighborCount = 0;
    int neighborTOut = 0;
    int neighCount = 0;
    int neighTOut = 0;
    int decidedCount = 0;
    int decidedTOut = 0;


    void set_motion(int new_motion)
    {
        if (curr_motion != new_motion)
        {
            curr_motion = new_motion;
            if (new_motion == STOP)
            {
                set_motors(0, 0);
            }
            else if (new_motion == FORWARD)
            {
                spinup_motors();
                set_motors(kilo_straight_left, kilo_straight_right);
            }
            else if (new_motion == LEFT)
            {
                spinup_motors();
                set_motors(kilo_turn_left, 0);
            }
            else
            { // RIGHT
                spinup_motors();
                set_motors(0, kilo_turn_right);
            }
        }
    }

    int cpd(int probe)
    {
      PyObject *sysPath, *pModule, *pName, *pFunc, *pArgs, *pSamples, *pValue;
      if (pyini == 0){
        Py_Initialize();
        import_array();
        printf("Python initialized\n");
      }
      int res = 0;
      sysPath = PySys_GetObject((char*)"path");
      PyList_Append(sysPath, (PyUnicode_FromString("/home/user/Desktop/Bayes Bots MA Kai Pfister/DynamicBayesBots CPD/dynamicEnvironments")));
      probes.push_back(probe);
      log_noCPD = 0;
      npy_intp dims[1];
      dims[0] = probes.size();
      if(dims[0]>1){//has to be >2*window_size for RuLSIF
        pName = PyUnicode_FromString("CPD");
        pModule = PyImport_Import(pName);
        pArgs = PyList_New(probes.size());
        for (size_t i = 0; i < probes.size(); ++i)
        {
            log_noCPD += probes[i];
            pValue = PyLong_FromLong(probes[i]);
            if (!pValue)
            {
                Py_DECREF(pArgs);
                printf("Cannot convert argument\n");

            }
            /* pValue reference stolen here: */
            PyList_SetItem(pArgs, i, pValue);
        }
        log_noCPD = log_noCPD/probes.size();
        pArgs = Py_BuildValue("(O)", pArgs);
        if(pModule)
        {
        	pFunc = PyObject_GetAttrString(pModule, "detectCP");
        	if(pFunc && PyCallable_Check(pFunc))
        	{
        		pValue = PyObject_CallObject(pFunc, pArgs);
            res = PyLong_AsLong(pValue);

            // When a vector with CP should be returned
            // std::vector<int> changePoints;
        		// if (PyList_Check(pValue) && PyList_Size(pValue)!=0) {
        		// 	for(Py_ssize_t i = 0; i < PyList_Size(pValue); i++) {
        		// 		PyObject *value = PyList_GetItem(pValue, i);
        		// 		changePoints.push_back( PyLong_AsLong(value) );
            //     cp.push_back( PyLong_AsLong(value) );
            //     printf("Method return = %d\n", changePoints[i]);
            //     Py_DECREF(value);
        		// 	}
        		// }
            Py_DECREF(pValue);
            Py_DECREF(pArgs);
            Py_DECREF(pFunc);
        	}
        	else
        	{
        		printf("ERROR: Method not found\n");
            Py_DECREF(pFunc);
            Py_DECREF(pArgs);
        	}
          Py_DECREF(pModule);
        }
        else
        {
        	printf("ERROR: Module not imported\n");
          Py_DECREF(pModule);
          Py_DECREF(pArgs);
        }
      }
      // printf("Method return = %d\n", res);
      return res;
    }

    /*
    Function proofs if environment has changed.
    The robot checks if its belive q falls below the threshold the pres after its previous decision (credible threshold was reached).
    If so reset.
    */
    void decision_Reset(int decision, double betaCDF)
    {
        if (decision > 0)
        {
            if ((1-betaCDF)<pres)
            {
                df = -1;
                dReset = 1;
            }
        }
        else if (decision == 0)
        {
            if (betaCDF<pres)
            {
                df = -1;
                dReset = 1;
            }
        }
    }


    // Reset of all parameters after a reset flag was set
    void reset()
    {
        dReset = 0;                       // Reset reset flag
        neighborCount = 0;
        neighCount = 0;
        countR ++;
        s.clear();                        // Clear the dictionary
        s_reset.clear();
        s_decided.clear();
        probes.clear();                   // Clear data frame
        cp.clear();                       // Clear CP dic
        m[3] = 5;
        m[4] = 0;
        transmit_msg.data[3] = 5;
        transmit_msg.data[4] = 0;
        df = -1;
        q = 0.5;
        alpha = alpha0;
        beta = alpha0;
        i = 0;
        set_color(RGB(q, 0.5, (1-q)));
    }


    void setup()
    {
        transmit_msg.type = NORMAL;
        transmit_msg.data[0] = 0;
        transmit_msg.data[3] = 5;
        transmit_msg.crc = message_crc(&transmit_msg);
        set_color(RGB(q, 0.5, (1-q)));
        set_motion(FORWARD);
        next_check_dur = 0;
        i = 0;
        m[4] = 0;
        m[3] = 5;
        alpha = alpha0;
        beta = alpha0;
        countR = 0;
        rw = 1;

    }


    void loop()
    {
        //check = q;                          // Debug variable
        log_q=q;
        log_df=df;
        log_res=countR;
        light_intensity = get_ambientlight();

        if (((light_intensity > 700) || (light_intensity < 300)))
        {
          if (light_intensity > 700)
          {
              log_C = 1;
          }
          else
          {
              log_C = 0;
          }
          // High frequency Change Detection
          // if(observe==true){
          //   probeC /= looprun;
          //   looprun = 0;
          //   if(probeC <= 0.5){
          //     probeC = 0;
          //   }
          //   else{
          //     probeC = 1;
          //   }
          //   cpd(probeC);
          //   pyini = 1;
          //   // check = cp[0];
          // }
          // else{
          //   looprun++;
          //   probeC += log_C;
          // }
        }

        // random walk
        if ((kilo_ticks > last_checked + next_check_dur)||((light_intensity < 700) && (light_intensity > 300)))
        {
            std::random_device rd;
            std::mt19937 gen(rd());
            std::exponential_distribution<> exp_dist(lambda); // Draw from an exponential distribution
            std::uniform_real_distribution<> uni_dist(0, 1);  // Draw from an uniform distribution
            double straigth_dur = exp_dist(gen);
            double turn_dur = (uni_dist(gen)*turn_max);	//robot turn speed 0.5 rad/s
            next_check_dur = 0;
            last_checked = kilo_ticks;

            // Turn to navigate out of the border (gray area)
            if ((light_intensity < 700) && (light_intensity > 300))
            {
                set_motion(RIGHT);
            }
            else if (rw == 1)
            {
                next_check_dur = int(-log((double)rand_hard() / 255.0) * (240*SECOND));
                set_motion(FORWARD);
                rw = 0;
            }
            else if(rw == 0)
            {
                if(uni_dist(gen))
                {
                  next_check_dur = turn_dur;
                  set_motion(RIGHT);
                }
                else
                {
                  next_check_dur = turn_dur;
                  set_motion(LEFT);
                }
                rw = 1;
            }
        }

        // Dictionary at the moment not in use. Idea: weight trustworthy Robots heigher?
        lock_dict = 1;
        if (new_message)
        {
            for (long unsigned int j=0; j<s.size();j++)
            {

            }
            new_message = 0;
        }
        lock_dict = 0;

//-----------------------------Experiments-----------------------------------//
        // 5) Positive Feedback: Recruitment of false decided
        if (kilo_ticks > (decidedTOut+300*SECOND) && decidedCount > 0)
        {
            if(kilo_ticks > (decidedTOut+300*SECOND))
            {
                decidedCount = 0;
                s_decided.clear();
            }
            decidedTOut = kilo_ticks;
        }
        if ((m[3]!=5) && (df!=-1) && (std::find(s_decided.begin(), s_decided.end(), m[0])== s_decided.end()))
        {
            s_decided.push_back(m[0]);

            // following is needed to assure only robots with same decision push the counter
            if(m[3] == 1)
            {
                decidedCount ++;
            }
            else if (m[3] == 0)
            {
                decidedCount --;
            }
            // if(id == 0 && abs(decidedCount)>=5){
            //   printf("Decided Count: %d at time %d", decidedCount, kilo_ticks*SECOND);
            // }
            if((abs(decidedCount) >= 10)){
              df = m[3];
              alpha = m[6];
              beta = m[7];
              // countR = m[5];
              decidedCount = 0;
              s_decided.clear();
            }
        }

        // 4c) Positive Feedback: Less aggressive Recruitment by more experienced (need X neigbors+id check)EXPERIMENT X
        if (kilo_ticks > (neighborTOut+50*SECOND) && neighborCount > 0)
        {
            if(kilo_ticks > (neighborTOut+50*SECOND))
            {
                neighborCount = 0;
                s.clear();
            }
            neighborTOut = kilo_ticks;
        }
        if ((m[3]!=5)&&(df==-1)&&(countR<=m[5]) && (std::find(s.begin(), s.end(), m[0])== s.end()))
        {
            s.push_back(m[0]);

            // following is needed to assure only robots with same decision push the counter
            if(m[3] == 1)
            {
                neighborCount ++;
            }
            else if (m[3] == 0)
            {
                neighborCount --;
            }

            if(abs(neighborCount) >= 5){
              df = m[3];
              alpha = m[6];
              beta = m[7];
              countR = m[5];
              neighborCount = 0;
              s.clear();
            }
        }

        // 4b) Positive Feedback: Thresholded recruitment by more experienced EXPERIMENT IX
        // if ((m[3]!=5)&&(df==-1)&&(countR<=m[5]))
        // {
        //     if(m[3]=0 && q > 0.6){
        //         df = m[3];
        //         alpha = m[6];
        //         beta = m[7];
        //         countR = m[5];
        //     }
        //     else if (m[3]=1 && q < 0.4){
        //         df = m[3];
        //         alpha = m[6];
        //         beta = m[7];
        //         countR = m[5];
        //     }
        // }

        // 4a) Positive Feedback: Recruitment by more experienced EXPERIMENT VII
        // if ((m[3]!=5)&&(df==-1)&&(countR<=m[5]))
        // {
        //     df = m[3];
        //     alpha = m[6];
        //     beta = m[7];
        //     countR = m[5];
        // }

        // 3d) Experiment VI but neighbors can also disseminate. EXPERIMENT VIII
        // if (kilo_ticks > (neighborTOut+50*SECOND) && neighborCount > 0)
        // {
        //     if(kilo_ticks > (neighborTOut+50*SECOND))
        //     {
        //         neighborCount = 0;
        //         s.clear();
        //     }
        //     neighborTOut = kilo_ticks;
        // }
        // if ((m[4]==1) && df!=-1 && (countR<=m[5]) && (std::find(s.begin(), s.end(), m[0])== s.end()))
        // {
        //     s.push_back(m[0]);
        //     neighborCount ++;
        //     if(neighborCount == 3){
        //         dReset = 1;
        //         receiveReset += 1;
        //     }
        // }

        // 3c) Experiment V but ID is checked. EXPERIMENT VI
        if (kilo_ticks > (neighTOut+50*SECOND) && neighCount > 0)
        {
            if(kilo_ticks > (neighTOut+50*SECOND))
            {
                neighCount = 0;
                s_reset.clear();
            }
            neighTOut = kilo_ticks;
        }
        if ((m[4]==1) && df!=-1 && (countR<=m[5]) && (std::find(s_reset.begin(), s_reset.end(), m[0])== s_reset.end()))
        {
            s_reset.push_back(m[0]);
            neighCount ++;
            if(neighCount >= 3){
                dReset = 1;
            }
        }

        // 3b): 2b) + 3a) Combination of Experiment III & IV. EXPERIMENT V
        // if (kilo_ticks > (neighborTOut+50*SECOND) && neighborCount > 0)
        // {
        //     neighborTOut = kilo_ticks;
        //     neighborCount = 0;
        // }
        // if ((m[4]==1)&& df>-1 )
        // {
        //     neighborCount ++;
        //     if(neighborCount == 3){
        //         dReset = 1;
        //     }
        // }

        // 2d) Dissemination only decided can be reset and neighbors can also disseminate but need 3 EXPERIMENT XII
        // if (m[4]==1 && df>-1 )
        // {
        //     receiveReset += 1;
        //     dReset = 1;
        // }

        // 2c) Dissemination only decided can be reset and neighbors can also disseminate EXPERIMENT XI
        // if (m[4]==1 && df>-1 )
        // {
        //     receiveReset = 3;
        //     dReset = 1;
        // }


        // 2b) Simple Dissemination but only decided can be reset EXPERIMENT IV
        // if (m[4]==1 && df>-1)
        // {
        //     dReset = 1;
        // }


        // 3a) Needs Neighbors Opinion to Disseminate within 50s EXPERIMENT III
        // if (kilo_ticks > (neighborTOut+50*SECOND) && neighborCount > 0)
        // {
        //     neighborTOut = kilo_ticks;
        //     neighborCount = 0;
        // }
        // if ((m[4]==1))
        // {
        //     neighborCount ++;
        //     if(neighborCount == 3){
        //         dReset = 1;
        //     }
        // }


        // 2a) Simple Dissemination EXPERIMENT II (Multiple Resets!!)
        // if ((m[4]==1))
        // {
        //     dReset = 1;
        // }


        // 1) No Dissemination EXPERIMENT I
        if (dReset == 1)
        {
            reset();
        }

//---------------------------------------------------------------------------//

        // Observation of tile below
        if ((observe == true) && ((light_intensity > 700) || (light_intensity < 300)))
        {
            observe = false;
            // light_intensity = get_ambientlight();

            if (light_intensity > 700)
            {
                C = 1;
            }
            else
            {
                C = 0;
            }

            alpha += C;
            beta += (1-C);
            i++;

            // Calculate the CDF
            q = boost::math::ibeta((double)alpha, (double)beta, (double)0.5);

            // Decision making
            if (df == -1){
                set_color(RGB(q, 0.5, (1-q)));

                if (q > pc)
                {
                    df = 0;
                    set_color(RGB(1, 0, 0));
                }
                else if ((1-q) > pc)
                {
                    df = 1;
                    set_color(RGB(0, 0, 1));
                }
            }

            // Check if a reset is needed (environment change)
            // decision_Reset(df, q);

            // CPD Reset
            dReset = cpd(C);
            pyini = 1;
            if(dReset == 1 || receiveReset == 3)
            {
                msgReset = 1;
                receiveReset = 0;
                last_res = kilo_ticks;
            }
            if ((msgReset == 1) && (kilo_ticks > last_res + res_dur))
              {
                  msgReset = 0;
              }
        }
    }


    // Prepare the message content
    void update_transmit_msg()
    {
        transmit_msg.type = NORMAL;
        transmit_msg.data[0] = id;
        transmit_msg.data[1] = i;
        if(df==-1){transmit_msg.data[3] = 5;}else{transmit_msg.data[3] = df;}
        transmit_msg.data[4] = msgReset;
        transmit_msg.data[5] = countR;
        transmit_msg.data[6] = alpha;
        transmit_msg.data[7] = beta;

        if (df != -1 && uPos)
            transmit_msg.data[2] = df;
        else
            transmit_msg.data[2] = C;

        transmit_msg.crc = message_crc(&transmit_msg);
    }


    // Receiving message
    void message_rx(message_t *msg, distance_measurement_t *dist)
    {
        if ((comm_criteria(*dist) == true) && (lock_dict==0))
        {
            m[0] = msg->data[0];    // robot id
            m[1] = msg->data[1];    // number of color observation
            m[2] = msg->data[2];    // color observation
            m[3] = msg->data[3];    // decision message
            m[4] = msg->data[4];    // reset message
            m[5] = msg->data[5];    // reset counter
            m[6] = msg->data[6];    // alpha
            m[7] = msg->data[7];    // beta

            new_message = 1;        // Set the flag to 1 to indicate a new message received
        }
    }

    // Sending message
    message_t *message_tx()
    {
        update_transmit_msg();
        return &transmit_msg;
    }

    void message_tx_success() {}
};
} // namespace Kilosim
