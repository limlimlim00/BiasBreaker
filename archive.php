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
    $stmt = $pdo->prepare("SELECT query, pdf_path, created_at FROM archive_list WHERE email = :email ORDER BY created_at DESC");
    $stmt->execute([':email' => $email]);
    $results = $stmt->fetchAll(PDO::FETCH_ASSOC);

    echo json_encode($results);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => '��ī�̺� �ҷ����� ����']);
}
