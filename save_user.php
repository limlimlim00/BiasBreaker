<?php
session_start();
header('Content-Type: application/json');

$data = json_decode(file_get_contents("php://input"), true);

if (!isset($data['email']) || !isset($data['name']) || !isset($data['picture'])) {
    http_response_code(400);
    echo json_encode(['error' => '�ʼ� ������ ����']);
    exit;
}

require_once 'db.php';

try {
    $stmt = $pdo->prepare(
        "INSERT INTO users (email, name, picture) 
         VALUES (:email, :name, :picture)
         ON DUPLICATE KEY UPDATE 
            name = VALUES(name), 
            picture = VALUES(picture), 
            last_login = NOW()"
    );
    $stmt->execute([
        ':email' => $data['email'],
        ':name' => $data['name'],
        ':picture' => $data['picture']
    ]);

    $_SESSION['user'] = [
        'email' => $data['email'],
        'name' => $data['name'],
        'picture' => $data['picture']
    ];

    echo json_encode(['ok' => true]);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'DB ���� ����', 'details' => $e->getMessage()]);
}
