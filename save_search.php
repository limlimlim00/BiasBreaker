<?php
ini_set('display_errors', 1);
error_reporting(E_ALL);
session_start();

header('Content-Type: application/json');
require_once __DIR__ . '/db.php';

// �α��� Ȯ��
if (!isset($_SESSION['user']) || !isset($_SESSION['user']['email'])) {
    http_response_code(403);
    echo json_encode(["error" => "�α����� �ʿ��մϴ�."]);
    exit;
}

$rawData = file_get_contents("php://input");
$data = json_decode($rawData, true);

// query �ʼ� üũ
if (!isset($data['query']) || trim($data['query']) === '') {
    http_response_code(400);
    echo json_encode(["error" => "�˻�� �������� �ʾҽ��ϴ�."]);
    exit;
}

$email = $_SESSION['user']['email'];

try {
    $stmt = $pdo->prepare("INSERT INTO search_history (email, query) VALUES (:email, :query)");
    $stmt->execute([
        ':email' => $email,
        ':query' => $data['query']
    ]);

    echo json_encode(["status" => "saved"]);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode([
        "error" => "�˻� ��� ���� �� ���� �߻�",
        "message" => $e->getMessage()
    ]);
}
