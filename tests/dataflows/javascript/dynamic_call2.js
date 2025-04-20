var dyn_functions = [];
dyn_functions['populate_Colours'] = function (arg1, arg2) { 
                // function body
           };
dyn_functions['populate_Shapes'] = function (arg1, arg2) { 
                // function body
           };

// calling one of the functions
var result = dyn_functions['populate_Shapes'](1, 2);
// this works as well due to the similarity between arrays and objects
var result2 = dyn_functions.populate_Shapes(1, 2);

