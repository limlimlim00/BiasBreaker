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
    // ★ id가 있을 때만 개별 삭제
    if (isset($data['id'])) {
        // (기존 코드 동일)
        $stmt = $pdo->prepare("SELECT pdf_path FROM archive_list WHERE id = :id AND email = :email");
        $stmt->execute([':id' => $data['id'], ':email' => $email]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);

        if ($row && file_exists($row['pdf_path'])) {
            unlink($row['pdf_path']);
        }

        $stmt = $pdo->prepare("DELETE FROM archive_list WHERE id = :id AND email = :email");
        $stmt->execute([':id' => $data['id'], ':email' => $email]);
    }
    // ★ id 없는 전체 삭제는 "명시적" 쿼리스트링 or 확인값 등으로 구분 (권장)
    else if (isset($data['delete_all']) && $data['delete_all'] === true) {
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
    else {
        // 잘못된 요청
        http_response_code(400);
        echo json_encode(['error' => '삭제할 id 또는 delete_all 플래그 필요']);
        exit;
    }

    echo json_encode(['ok' => true]);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'DB 처리 오류']);
}

