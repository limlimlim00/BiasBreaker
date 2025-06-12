<?php
require_once 'db.php';
session_start();
header('Content-Type: application/json');

$data = json_decode(file_get_contents("php://input"), true);
if (!isset($_SESSION['user']['email']) || !isset($data['query']) || !isset($data['html'])) {
    http_response_code(400);
    echo json_encode(['error' => 'µ¥ÀÌÅÍ ´©¶ô']);
    exit;
}

$email = $_SESSION['user']['email'];
$query = $data['query'];
$html = $data['html'];

// ÀúÀå °æ·Î ¼³Á¤
$sanitizedQuery = preg_replace('/[^a-zA-Z0-9°¡-ÆR]/u', '_', $query);
$timestamp = date("Ymd_His");

$filename = $sanitizedQuery . "_" . $timestamp . ".pdf";
$relativePath = "archives/" . $filename;
$absolutePath = __DIR__ . '/' . $relativePath;

require 'vendor/autoload.php';

use Dompdf\Dompdf;
use Dompdf\Options;

$options = new Options();
$options->set('isRemoteEnabled', true);  // ¿ÜºÎ ÀÌ¹ÌÁö µî Çã¿ë
$dompdf = new Dompdf($options);
$dompdf->loadHtml($html);
$dompdf->setPaper('A4', 'portrait');
$dompdf->render();

// PDF ÀúÀå
file_put_contents($absolutePath, $dompdf->output());

// DB ÀúÀå
$stmt = $pdo->prepare("INSERT INTO archive_list (email, query, pdf_path) VALUES (:email, :query, :path)");
$stmt->execute([
  ':email' => $email,
  ':query' => $query,
  ':path' => $relativePath  // »ó´ë °æ·Î·Î ÀúÀå
]);

echo json_encode(['ok' => true, 'pdf' => $relativePath]);
