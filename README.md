# Trade Logic
Bu repo, elimizdeki sinyalleri toplayıp ana mantığı uygulayacağımız ve al sat yapacak end pointi tetikleyecek
kodun yazıldığı repodur.


Binance'e baglanmak icin `API_KEY` = "xxxx" `API_SECRET` = "xxxxxx" degiskenleri config.py dosyasina 
koyarak debug yapabilirsiniz.

# AWS EC2 instance'a baglanma
EC2 instance olustur, default degerler ile ilerle
Son adimlarda ssh key indirmen gerekecek, duzgun bir isim ver ve dosyayi indir

Security group'lardan ilgili gruba inbound SSH roule ekle kendi ip'in icin, ip'in degisirse burayi guncellemen gerekir

Public DNS icin instance'a girdikten sonra baglan(connect) tusundan ssh secenegine bakabilirsiniz.
`ssh -i "<anahtar dosya path'i>" <kullanici_adi>@<Public DNS>`

`scp -i "<anahtar dosya path'i>" <config.py_dosyasina_path> <kullanici_adi>@<Public DNS>:<trade_logic_repo_path>`
