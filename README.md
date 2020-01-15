# Hallo, nama saya Kirana

Dulu (bahkan mungkin) sampai saat ini Linux masih agak sulit bagi pemula. Dapat dipahami sebab hingga saat ini seorang pengguna Linux masih lebih sering berkutat dilayar konsole, lebih sering mengetik perintah, lebih banyak menggunakan keyboard daripada mouse dan lain-lain.

Selain itu pemahaman yang kurang tepat ketika seorang baru belajar Linux adalah diharuskan menghapal semua perintah yang ada di Linux. Ya terus terang itu adalah ide yang gila. Sebab saat ini Linux memiliki lebih dari 1000 perintah dan lebih dari 2000 opsi dari perintah-perintah yang ada tersebut. 

### Menghancurkan dinding komunikasi

Saat ini, apapun sistem operasi yang anda gunakan. Terlebih apabila anda lebih banyak berkutat dengan *command line*. Kita seperti 'diwajibkan' untuk mempelajari bahasa mereka. Ini yang menjadi aneh buat kami. Sebab kami percaya, justru mereka (baca: sistem) yang mengerti kemauan kita. Bukan sebaliknya. 

__Kirana__, hadir untuk membantu menterjemahkan perintah dari pengguna ke mesin. Dia yang akan menghancurkan dinding komunikasi yang ada saat ini antara pengguna Linux dengan sistemnya sendiri.

### Jalanin secara container - BIG Mode

Kirana juga punya kok nih versi containernya. Jadi sudah container-based ready. Mau sebagai CI/CD ala DevOps, ayuk.

DevSecOps? Kirana juga siap. Saat ini didalamnya ada. Nanti tinggal jalanin tools ini didalam pipeline:
* nmap
* SSLyze
* Owasp ZAP
* zap-cli
* tcping
* tcptraceroute / traceroute / dnsutils

Nah kalo mau coba jalanin sebagai container stand alone. Jalanin aja command ini,

```
docker run -ti --user soekir:soekir ajobondon/kirana bash
```

Nanti kakak akan "login" sebagai user *soekir* dan silakan mulai "chat" dengan Kirana ya.

### Jalanin secara container - SLIM Mode

Kirana juga bisa diet kok. Ini udah disiapkan slim modenya ya. Untuk buildnya bisa pakai cara,

```
docker build -t <nama-image-bebas> -f Dockerfile-slim
```

Atau kalau males build. Bisa aja tinggal pull dari hub.docker.com kok. Caranya,

```
docker pull ajobondon/kirana:slim
```

Kirana slim mode ini untuk saat ini, hanya berisikan tools,

* TCPing
* nmap (nmap script support)
* tcptraceroute
* traceroute

Nanti kalo ada update lainnya, pasti akan dilist disini. 

Selain itu slim mode ini cocok untuk kebutuhan yang straight forward. Quick scan atau bisa dimasukan ke Jenkins pipeline misalnya. Oleh karena itu memang slim mode ini sengaja dan dimaintain akan tetap kecil ukuran filenya. 

### Install - stand alone mode

Silakan download file ini, [installer](https://goo.gl/FVFAUu).
Untuk saat ini Kirana __hanya bisa diinstall di Debian dan Ubuntu__ saja. Untuk distribusi Linux lainnya akan menyusul.

Download dan simpan file tersebut ditempat yang kamu inginkan. 
Sebagai contoh kamu simpan file itu di folder Downloads. Kemudian masuk ke folder tersebut dan jalankan perintah sebagai berikut, 

```
chmod +x installer
sh installer
```

Sebagai catatan, harap jangan menginstall __Kirana__ sebagai user root. Cukup dengan menggunakan user kamu saja.

### Cara pakenya?

Mirip seperti anda *chatting* dengan teman. Contoh,
* Perintah untuk lihat list file/folder
  * liat
* Perintah untuk install aplikasi
  * kirana install aplikasi <nama_aplikasi>
* Perintah untuk mengupdate Kirana 
  * kirana saatnya belajar
* Perintah SUDO atau login sebagai root
  * kirana saya takeover ya
* Perintah anti bingung
  * kiranya caranya <apa_aja> gimana ya

### Ah bingung mau mulai dari mana. Mau tanya apa.

Pada dasarnya pengguna yang berinteraksi dengan __Kirana__ bebas saja, mau memberikan perintah seperti apa. Nanti dia yang akan membantu menerjemahkan ke system. Kalo masih bingung bisa bilang aja ke dia,

__kirana caranya salin file itu gimana ya__

Atau apa saja, bebas. Sebab __Kirana__ ingin dianggap sebagai teman. Bukan system yang bersifat kaku. Jadi mulailah berbicara dengan dia seperti layaknya kita berbicara dengan teman.

### Ah payah nih. Masak dia nggak tau gue kasih perintah apa sih?!

Ya usia __Kirana__ saat ini memang masih bayi. Masih belum banyak kosakata yang bisa dimengerti. Oleh karena itu apabila kamu memang ingin buru-buru. Bisa *take over* dia. Caranya? Bilang aja ke dia, __"kirana saya takeover ya"__. Gampang kan? 

### Versioning?

Seperti layaknya manusia. Kirana tidak memiliki versioning seperti aplikasi lainnya. Namun __Kirana__ menggunakan umur. Penasaran? Coba tanya ke dia. __"kirana usia kamu berapa"__. Oleh karena itu rajin-rajinlah untuk menyuruh dia belajar. Caranya? Bilang aja, __"kirana saatnya belajar"__.

### Trus dia lahirnya kapan?

Dia lahir pada __19 Oktober 2015__

### Saya juga mau membantu mengasuh dia...

Dengan sangat senang hati. Kamu bisa mem-forknya atau mengirimkan request sebagai contributor. 

### Jadi dia cuma bisa gitu doank? Cemen...

Seperti layaknya manusia. __Kirana__ akan terus berkembang. Dia masih bayi, masih belajar mendengar dan berbicara. Memang masih belum banyak kosakata yang ia mengerti. Namun sekali lagi, dia masih akan terus belajar, sampai ajal menjemputnya....
