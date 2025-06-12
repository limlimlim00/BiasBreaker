<?php
session_start();
header('Content-Type: application/json');
require_once 'db.php';

// 로그인 확인
if (!isset($_SESSION['user'])) {
    http_response_code(401);
    echo json_encode(['error' => '로그인 필요']);
    exit;
}

$email = $_SESSION['user']['email'];

try {
    $stmt = $pdo->prepare("DELETE FROM search_history WHERE email = :email");
    $stmt->execute([':email' => $email]);

    echo json_encode(['ok' => true, 'message' => '검색 기록이 삭제되었습니다.']);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => '기록 삭제 실패']);
}
