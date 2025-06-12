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
    if (isset($data['id'])) {
        // Ư�� ��ī�̺� �ϳ� ����
        $stmt = $pdo->prepare("SELECT pdf_path FROM archive_list WHERE id = :id AND email = :email");
        $stmt->execute([':id' => $data['id'], ':email' => $email]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);

        if ($row && file_exists($row['pdf_path'])) {
            unlink($row['pdf_path']); // ���� ����
        }

        $stmt = $pdo->prepare("DELETE FROM archive_list WHERE id = :id AND email = :email");
        $stmt->execute([':id' => $data['id'], ':email' => $email]);
    } else {
        // ��ü ����: ��� PDF ��� ������ ����
        $stmt = $pdo->prepare("SELECT pdf_path FROM archive_list WHERE email = :email");
        $stmt->execute([':email' => $email]);
        while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
            if (file_exists($row['pdf_path'])) {
                unlink($row['pdf_path']);
            }
        }

        $stmt = $pdo->prepare("DELETE FROM archive_list WHERE email = :email");
        $stmt->execute([':email' => $email]);
    }

    echo json_encode(['ok' => true]);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'DB ���� ����']);
}
