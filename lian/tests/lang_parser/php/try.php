<?php
try {
  throw new Exception("This is an exception");
} catch(Exception $e) {
  echo $e->getMessage();
}
?>