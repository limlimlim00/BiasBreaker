<?php
session_start();
header('Content-Type: application/json');

require_once __DIR__ . '/db.php';

if (!isset($_SESSION['user'])) {
    http_response_code(401);
    echo json_encode(['error' => '로그인이 필요합니다.']);
    exit;
}

$email = $_SESSION['user']['email'];
$raw = file_get_contents("php://input");
$data = json_decode($raw, true);

try {
    
    if (isset($data['id'])) {
        $stmt = $pdo->prepare("DELETE FROM search_history WHERE id = :id AND email = :email");
        $stmt->execute([':id' => $data['id'], ':email' => $email]);
    }
    
    else if (isset($data['delete_all']) && $data['delete_all'] === true) {
        $stmt = $pdo->prepare("DELETE FROM search_history WHERE email = :email");
        $stmt->execute([':email' => $email]);
    }
    
    else {
        http_response_code(400);
        echo json_encode(['error' => '필수값 id 또는 delete_all 필드 필요']);
        exit;
    }

    echo json_encode(['ok' => true]);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'DB ó�� ����']);
}
