<?php
session_start();
header('Content-Type: application/json');

require_once 'db.php';

// 로그인 여부 확인
if (!isset($_SESSION['user']) || !isset($_SESSION['user']['email'])) {
    http_response_code(401);
    echo json_encode(['error' => '로그인 필요']);
    exit;
}

$email = $_SESSION['user']['email'];

try {
    $stmt = $pdo->prepare("SELECT id, query, searched_at FROM search_history WHERE email = :email ORDER BY searched_at DESC");
    $stmt->execute([':email' => $email]);
    $history = $stmt->fetchAll(PDO::FETCH_ASSOC);

    echo json_encode($history);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => '기록 조회 실패', 'message' => $e->getMessage()]);
}
