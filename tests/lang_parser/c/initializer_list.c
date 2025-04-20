int array[5] = {1, 2, 3, 4, 5};

int array[5] = {
    [0] = 1,
    [1] = 2,
    [2] = 3,
    [3] = 4,
    [4] = 5
};

int array[10] = {
    [0 ... 4] = 1,
    [5 ... 9] = 2
};

struct Point p = {
    x: 10,
    y: 20
};

struct Shape rect1 = {
    .top_left = { .x = 0, .y = 0 },
    .bottom_right = { .x = 10, .y = 10 }
},
rect2 = {
    .top_left = { .x = 10, .y = 10 },
    .bottom_right = { .x = 20, .y = 20 }
};