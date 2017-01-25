echo 'compiling with cython...';
cython -3 game/reversi.pyx -o game/reversi.c;
cython -3 game/board.pyx -o game/board.c;

echo 'removing old .so files...';
rm *.so agents/*.so game/*.so;

echo 'compiling .c files with gcc...'
gcc -shared `python3-config --includes` -fPIC `python3-config --ldflags` -pthread -fwrapv -O3 -Wall -fno-strict-aliasing game/reversi.c -o game/reversi.so;
gcc -shared `python3-config --includes` -fPIC `python3-config --ldflags` -pthread -fwrapv -O3 -Wall -fno-strict-aliasing game/board.c -o game/board.so; 

echo 'removing .c files...';
rm *.c agents/*.c game/*.c;

echo 'done.';

