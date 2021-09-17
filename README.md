# fbx_test_task

developed and tested on ubuntu linux 20.04 + blender

USAGE: /worker/run.sh --file (text file with urls) --out (output folder to store processed files)

HOW TO TEST(run shell scripts in their directories):

- clone repository

- create and activate virtual env

- start test backend server
    command: /backend/run.sh

- test_example.txt contains links to task archives, 1 broken link, 1 non-existing link

- start worker
    command: /worker/run.sh
    working example: ./worker/run.sh --file $PWD/test_example.txt --out $PWD/output