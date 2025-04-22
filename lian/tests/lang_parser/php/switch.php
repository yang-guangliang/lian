<?php
// $d = 4;

// switch ($d) {
//   case 6:
//     echo 'Today is Saturday';
//     break;
//   case 0:
//     echo 'Today is Sunday';
//     break;
//   default:
//     echo 'Looking forward to the Weekend';
// }

// $day = 'Monday'; // 假设 $day 的值是 Monday

$numLetters = match($day) {
    'Monday', 'Friday', 'Sunday' => 6,
    'Tuesday' => 7,
    'Wednesday' => 9,
    default => 0, // 如果没有匹配到任何 case，则返回 0
};

// function determineRole(int $level): string {
//     return match ($level) {
//         1, 2, 3 => "新手",
//         4, 5, 6 => "进阶",
//         7, 8, 9 => "专家",
//         default => "未知等级",
//     };
// }

// $userLevel = 5;
// echo "用户等级: " . determineRole($userLevel); // 输出 "用户等级: 进阶"

?>