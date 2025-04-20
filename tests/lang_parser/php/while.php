<?php
$i = 0;
while ($i < 6) {
  $i++;
  if ($i == 3) continue;
  echo $i;
}

do {
    echo $i;
    $i++;
  } while ($i < 6);
?>