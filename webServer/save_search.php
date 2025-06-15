<?php
ini_set('display_errors', 1);
error_reporting(E_ALL);
session_start();

header('Content-Type: application/json');
require_once __DIR__ . '/db.php';


if (!isset($_SESSION['user']) || !isset($_SESSION['user']['email'])) {
    http_response_code(403);
    echo json_encode(["error" => "로그인이 필요합니다."]);
    exit;
}

$rawData = file_get_contents("php://input");
$data = json_decode($rawData, true);


if (!isset($data['query']) || trim($data['query']) === '') {
    http_response_code(400);
    echo json_encode(["error" => "검색어가 입력되지 않았습니다."]);
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
        "error" => "검색 기록 저장 중 오류 발생",
        "message" => $e->getMessage()
    ]);
}
