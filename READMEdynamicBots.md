You can change the parameter in the dynamicEnvironments-directory in the
Config.json

To run the Kilosim with dynamic environments go to the build-directory and compile the program with:
$ cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_INSTALL_PREFIX=../ ..
$ make
$ make install


Go back to the source-directory:
$ cd ..


To run the simulation enter:
./bin/dynamic_bayesBots dynamicEnvironments/Config.json


After the run you can plot your Data by starting the show_h5.py:
$python3 show_h5.py test-log.h5

