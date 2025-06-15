<?php
session_start();
header('Content-Type: application/json');

require_once __DIR__ . '/db.php';

if (!isset($_SESSION['user'])) {
    http_response_code(401);
    echo json_encode(['error' => '�α����� �ʿ��մϴ�.']);
    exit;
}

$email = $_SESSION['user']['email'];
$raw = file_get_contents("php://input");
$data = json_decode($raw, true);

try {
    // ? ���� ���� (id ������)
    if (isset($data['id'])) {
        $stmt = $pdo->prepare("DELETE FROM search_history WHERE id = :id AND email = :email");
        $stmt->execute([':id' => $data['id'], ':email' => $email]);
    }
    // ? ��ü ���� (��������� delete_all = true ���޵�)
    else if (isset($data['delete_all']) && $data['delete_all'] === true) {
        $stmt = $pdo->prepare("DELETE FROM search_history WHERE email = :email");
        $stmt->execute([':email' => $email]);
    }
    // ?? �� �� �߸��� ��û
    else {
        http_response_code(400);
        echo json_encode(['error' => '������ id �Ǵ� delete_all �÷��� �ʿ�']);
        exit;
    }

    echo json_encode(['ok' => true]);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'DB ó�� ����']);
}
