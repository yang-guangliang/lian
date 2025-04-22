<?php  
$array = array(1, 2, 3); 

print_r($array);
// foreach ($array as $a) {
//   echo $a . "\n";
// }
foreach ($array as $key => $value) {
  echo $key . ": " . $value . "\n";
}

$receiver = [
  "k1" => "1",
  "k2" => 2
];

// foreach ($receiver as $key => $value) {
//   echo $key . ": " . $value . "\n";
// }

foreach ($receiver as $a) {
  echo $a . "\n";
}
?>  