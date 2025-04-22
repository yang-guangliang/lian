<?php

// if ($a > $b) {}

// if ($a + $b > $c) {}

// $score = 85;

if ($score >= 60) {
    echo "You passed the exam.\n";

    if ($score >= 90) {
        echo "Excellent!\n";
    } elseif ($score >= 80) {
        echo "Very Good!\n";
    } elseif ($score >= 70) {
        echo "Good job!\n";
    } else {
        echo "You passed, but there's room for improvement.\n";
    }
} else {
    echo "Unfortunately, you failed.\n";

    // 在 else 块中继续使用 if 和 elseif
    if ($score >= 50) {
        echo "You were close to passing.\n";
    } elseif ($score >= 40) {
        echo "You need some more practice.\n";
    } elseif ($score >= 30) {
        echo "??????.\n";
    } else {
        echo "You need significant improvement.\n";
    }
}

// if( $a == 1 || $a == 2 ) {

//     if( $b == 3 || $b == 4 ) {

//         if( $c == 5 || $d == 6 ) {

//              //Do something here.

//         }

//     }

// } elseif($a) {
// 	if ($b) {}
// } elseif ($b) {

// }
// elseif ($b) {

// } else {
//     $c = 1;
// }

// $a = 4;
// if($a < 5):
//   echo "Less than five";
// elseif($a < 10):
//   echo "More than five but less than ten";
// elseif($a >= 20):
//   echo "Greater than 20";
// else:
//   echo "Greater than ten";
// endif;

?>
