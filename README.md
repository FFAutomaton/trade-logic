# Trade Logic
Bu repo, elimizdeki sinyalleri toplayıp ana mantığı uygulayacağımız ve al sat yapacak end pointi tetikleyecek
kodun yazıldığı repodur.


Binance'e baglanmak icin `API_KEY` = "xxxx" `API_SECRET` = "xxxxxx" degiskenleri config.py dosyasina 
koyarak debug yapabilirsiniz.

### ENV 
PYTHON_ENV = "TEST". Bunu degiskenlerinize local denemelerinizde ekleyin. Botu calistirirken bu degiskeni TEST harici birsey yapabilirsiniz.

## Localde calistirma
`Dockerfile` ve `bash_scripts` kalsoru altindaki scriptlerdeki path giti degiskenlerin dogrulugundan emin olun.

`rebuild.sh` dosyasini executable hale getirin, sonrasinda `./bash_scripts/rebuild.sh` komutu ile docker container icinde 
botu calistirabilirsiniz.

`docker ps` komutu ile `trader-bot` container id'yi cekin ve container'a baglanin. `app` klasoru icinde `main.py` 
dosyasini calistirarak calistigindan emin olun.

Calisan container'in id'sini alip asagidaki komuta ekleyerek container'a baglanabilirsin.
`docker ps`
```commandline
docker container exec -it <container_id> /bin/bash
docker container exec -it 9d81461c9338 /bin/bash
```

# AWS EC2 instance'a baglanma
EC2 instance olustur, default degerler ile ilerle, sadece disk size arttirabilirsin,
eger bunu yaparsen docker ayarlarinda volume arttirma adimlarini gecebilirsin.

Son adimlarda ssh key indirmen gerekecek, duzgun bir isim ver ve dosyayi indir

Security group'lardan ilgili gruba inbound SSH roule ekle kendi ip'in icin, ip'in degisirse burayi guncellemen gerekir,
istersen burayi her IP'ye izin verecek sekilde ayarlayabilirsin, SSH keylerin gerekli guvenligi saglayacaktir.

Public DNS icin instance'a girdikten sonra baglan(connect) tusundan ssh secenegine bakabilirsiniz.
`ssh -i "<anahtar dosya path'i>" <kullanici_adi>@<Public DNS>`

`scp -i "<anahtar dosya path'i>" <config.py_dosyasina_path> <kullanici_adi>@<Public DNS>:<trade_logic_repo_path>`
`scp -i "trade-bot.pem" /Users/sevki/Documents/repos/turkish-gekko-organization/trade-logic/config.py ubuntu@ec2-54-173-54-47.compute-1.amazonaws.com:/home/ubuntu/trade-logic`
## EC2'ye docker yukleme
Sirasiyla su komutlari calistirin
`curl -fsSL https://get.docker.com -o get-docker.sh`
`sh get-docker.sh`

## Docker islemleri

Docker islemlerine baslamak icin `Dockerfile` dosyasinin dogru ve duzgun calistigindan emin olun

Docker dosyamizi container icinde cron calisacak hale getirdik. Bu sayade olayin akisi tamamen container
icinde devam edecek. loglari da disari bir dosyaya yazacak bir kodu ekledik.
Ayrintilar icin: https://github.com/mloning/minimal-python-app-using-docker-cron

- Once docker `build` alalim, uygulamanin ana klasorunde
```
docker build --rm -t trade-bot .
```

- Sonra bu `docker goruntusunu` gene bu klasore kaydedelim
`docker save trade-bot > prophet-trader.tar`
- Bu olusumu aktarabilmek icin once s3 bucket'ina yuklemek gerekiyor, gerekli ayarlar icin:
`https://aws.amazon.com/tr/premiumsupport/knowledge-center/ec2-instance-access-s3-bucket/`
- Paralel yükleme yapmak içim aks cli'nin gerekli değişkenlerini ayarlıyoruz, detayları şu linkte bulabilirsiniz:
https://aws.amazon.com/tr/premiumsupport/knowledge-center/s3-multipart-upload-cli/
`aws s3 cp /Users/sevki/Documents/repos/turkish-gekko-organization/trade-logic/prophet-trader.tar s3://prophet-trader/ --metadata md5="examplemd5value1234/4Q"`
- Sonrasinda s3'den dosyayi ec2 instance'a cekiyoruz, once makineye baglanip su kodu calistiralim
`aws s3 cp s3://prophet-trader/prophet-trader.tar ./`
- Imajimizi docker'a yuklemeden once ek olarak sabit disk eklemek gerekiyor, volume modify kismindan disk size'i 
arttiralim. Eger makineyi kaldirirken disk buyuk secildiyse bu adim atlanabilir
- tar dosyasini acip docker'a yukleyelim
`docker load < prophet-trader.tar`
- En son islemlerden sonra olay calistirmaya geldi
```commandline
docker run -t -i -d --rm \
    --name trade-bot -v /home/sevki/Documents/repos/turkish-gekko/trade-logic/trade-bot-logs:/output \
     -v /home/sevki/Documents/repos/turkish-gekko/trade-logic/coindata/ETHUSDT.db:/app/coindata/ETHUSDT.db \
     prophet-trader
```

Ek linkler:
https://stackoverflow.com/questions/41782038/how-to-move-docker-containers-to-aws
