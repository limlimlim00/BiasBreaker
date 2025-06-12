<?php
session_start();
header('Content-Type: application/json');
require_once 'db.php';

// �α��� Ȯ��
if (!isset($_SESSION['user'])) {
    http_response_code(401);
    echo json_encode(['error' => '�α��� �ʿ�']);
    exit;
}

$email = $_SESSION['user']['email'];

try {
    $stmt = $pdo->prepare("DELETE FROM search_history WHERE email = :email");
    $stmt->execute([':email' => $email]);

    echo json_encode(['ok' => true, 'message' => '�˻� ����� �����Ǿ����ϴ�.']);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => '��� ���� ����']);
}
