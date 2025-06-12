<?php
ini_set('display_errors', 1);
error_reporting(E_ALL);
session_start();

require_once __DIR__ . '/db.php';

if (!isset($_SESSION['user'])) {
    http_response_code(403);
    echo json_encode(["error" => "Not logged in"]);
    exit;
}

$rawData = file_get_contents("php://input");
$data = json_decode($rawData, true);

if (!isset($data['query'])) {
    http_response_code(400);
    echo json_encode(["error" => "No query provided"]);
    exit;
}

$userId = $_SESSION['user']['id'] ?? null;
if (!$userId) {
    http_response_code(403);
    echo json_encode(["error" => "User ID not found in session"]);
    exit;
}

$stmt = $pdo->prepare("INSERT INTO search_history (user_id, query) VALUES (?, ?)");
$stmt->execute([$userId, $data['query']]);

echo json_encode(["status" => "saved"]);
?>
