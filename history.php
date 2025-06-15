<?php
session_start();
header('Content-Type: application/json');

require_once 'db.php';

// �α��� ���� Ȯ��
if (!isset($_SESSION['user']) || !isset($_SESSION['user']['email'])) {
    http_response_code(401);
    echo json_encode(['error' => '�α��� �ʿ�']);
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
    echo json_encode(['error' => '��� ��ȸ ����', 'message' => $e->getMessage()]);
}
