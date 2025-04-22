<?php

$name = "Quincy";

echo "Hi! My name is " . $name . ".\n";
echo "Hi! My name is $name.\n";

class Car {
    function Car() {
        $this->model = "Tesla";
    }
}

// create an object
$Lightning = new Car();

// show object properties
echo $Lightning->model;

$colors = array("Magenta", "Yellow", "Cyan");

// prints: mysql link
$c = mysql_connect();
echo get_resource_type($c) . "\n";

// prints: stream
$fp = fopen("foo", "w");
echo get_resource_type($fp) . "\n";

// prints: domxml document
$doc = new_xmldoc("1.0");
echo get_resource_type($doc->doc) . "\n";


switch ($i) {
case "free":
    echo "i is free";
    break;
case "code":
    echo "i is code";
    break;
case "camp":
    echo "i is camp";
    break;
default:
    echo "i is freecodecamp";
    break;
}

for($index = 0; $index < 5; $index ++)
{
    echo "Current loop counter ".$index.".\n";
}

$index = 10;
while ($index >= 0)
{
    echo "The index is ".$index.".\n";
    $index--;
}

do
{
    // execute this at least 1 time
    echo "Index: ".$index.".\n"; 
    $index --;
}
while ($index > 0);

function say_hello() {
    return "Hello!";
}

function makeItBIG($a_lot_of_names) {
    foreach($a_lot_of_names as $the_simpsons) {
        $BIG[] = strtoupper($the_simpsons);
    }
    return $BIG;
}

$firstName = $_GET['firstName']

if(isset($firstName)){
    echo "firstName field is set". "<br>";
}
else{
    echo "The field is not set."."<br>";
}

?>
