<?php 

	// Function to check even or not 
	function checkEvenOrNot($num) { 
		if ($num % 2 == 0) 
		
			// Jump to even 
			goto even; 
		else
			// Jump to odd 
			goto odd; 

		even: 
			echo $num . " is even"; 
			
			// Return if even 
			return; 
		odd: 
			echo $num . " is odd"; 
	} 

	$num = 26; 
	checkEvenOrNot($num); 

?>
