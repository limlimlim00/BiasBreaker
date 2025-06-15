<?php
require_once 'db.php';
session_start();
header('Content-Type: application/json');

$data = json_decode(file_get_contents("php://input"), true);
if (!isset($_SESSION['user']['email']) || !isset($data['query']) || !isset($data['html'])) {
    http_response_code(400);
    echo json_encode(['error' => '필수값 누락']);
    exit;
}

$email = $_SESSION['user']['email'];
$query = $data['query'];
$html = $data['html'];

// 파일 이름 생성
$sanitizedQuery = preg_replace('/[^a-zA-Z0-9가-힣]/u', '_', $query);
$timestamp = date("Ymd_His");
$filename = $sanitizedQuery . "_" . $timestamp . ".pdf";
$relativePath = "archives/" . $filename;
$absolutePath = __DIR__ . '/' . $relativePath;

require 'vendor/autoload.php';

use Dompdf\Dompdf;
use Dompdf\Options;

$options = new Options();
$options->set('isRemoteEnabled', true);
$options->setChroot(__DIR__);  // Dompdf 보안제한 경로 설정

$dompdf = new Dompdf($options);

// 한글 폰트 스타일 삽입 (chroot 내 경로여야 함)
$fontFace = <<<HTML
<style>
@font-face {
  font-family: 'NotoSansKR';
  font-style: normal;
  font-weight: normal;
  src: url('fonts/NotoSansKR-Regular.ttf') format('truetype');
}
body, * {
  font-family: 'NotoSansKR', sans-serif !important;
}
</style>
HTML;

$htmlWithFont = $fontFace . $html;

$dompdf->loadHtml($htmlWithFont);
$dompdf->setPaper('A4', 'portrait');
$dompdf->render();

// PDF 파일 저장
file_put_contents($absolutePath, $dompdf->output());

// DB 저장
$stmt = $pdo->prepare("INSERT INTO archive_list (email, query, pdf_path) VALUES (:email, :query, :path)");
$stmt->execute([
    ':email' => $email,
    ':query' => $query,
    ':path' => $relativePath
]);

echo json_encode(['ok' => true, 'pdf' => $relativePath]);
