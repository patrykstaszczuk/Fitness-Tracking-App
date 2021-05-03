-- MySQL dump 10.13  Distrib 8.0.24, for macos11 (x86_64)
--
-- Host: localhost    Database: Przepisy_REST
-- ------------------------------------------------------
-- Server version	8.0.24

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=41 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add content type',4,'add_contenttype'),(14,'Can change content type',4,'change_contenttype'),(15,'Can delete content type',4,'delete_contenttype'),(16,'Can view content type',4,'view_contenttype'),(17,'Can add session',5,'add_session'),(18,'Can change session',5,'change_session'),(19,'Can delete session',5,'delete_session'),(20,'Can view session',5,'view_session'),(21,'Can add my user',6,'add_myuser'),(22,'Can change my user',6,'change_myuser'),(23,'Can delete my user',6,'delete_myuser'),(24,'Can view my user',6,'view_myuser'),(25,'Can add ingredient',7,'add_ingredient'),(26,'Can change ingredient',7,'change_ingredient'),(27,'Can delete ingredient',7,'delete_ingredient'),(28,'Can view ingredient',7,'view_ingredient'),(29,'Can add recipe',8,'add_recipe'),(30,'Can change recipe',8,'change_recipe'),(31,'Can delete recipe',8,'delete_recipe'),(32,'Can view recipe',8,'view_recipe'),(33,'Can add ingredient quantity',9,'add_ingredientquantity'),(34,'Can change ingredient quantity',9,'change_ingredientquantity'),(35,'Can delete ingredient quantity',9,'delete_ingredientquantity'),(36,'Can view ingredient quantity',9,'view_ingredientquantity'),(37,'Can add tag',10,'add_tag'),(38,'Can change tag',10,'change_tag'),(39,'Can delete tag',10,'delete_tag'),(40,'Can view tag',10,'view_tag');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `authtoken_token`
--

DROP TABLE IF EXISTS `authtoken_token`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `authtoken_token` (
  `key` varchar(40) NOT NULL,
  `created` datetime(6) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`key`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `authtoken_token_user_id_35299eff_fk_users_myuser_id` FOREIGN KEY (`user_id`) REFERENCES `users_myuser` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `authtoken_token`
--

LOCK TABLES `authtoken_token` WRITE;
/*!40000 ALTER TABLE `authtoken_token` DISABLE KEYS */;
INSERT INTO `authtoken_token` VALUES ('f322c679053f2ca2d0439ccd55ad16228c8ba22d','2021-05-03 08:09:53.921212',1);
/*!40000 ALTER TABLE `authtoken_token` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_users_myuser_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_users_myuser_id` FOREIGN KEY (`user_id`) REFERENCES `users_myuser` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'contenttypes','contenttype'),(7,'recipe','ingredient'),(9,'recipe','ingredientquantity'),(8,'recipe','recipe'),(10,'recipe','tag'),(5,'sessions','session'),(6,'users','myuser');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2021-03-29 13:29:34.277277'),(2,'contenttypes','0002_remove_content_type_name','2021-03-29 13:29:34.376939'),(3,'auth','0001_initial','2021-03-29 13:29:38.947269'),(4,'auth','0002_alter_permission_name_max_length','2021-03-29 13:29:39.290369'),(5,'auth','0003_alter_user_email_max_length','2021-03-29 13:29:39.302479'),(6,'auth','0004_alter_user_username_opts','2021-03-29 13:29:39.314033'),(7,'auth','0005_alter_user_last_login_null','2021-03-29 13:29:39.326050'),(8,'auth','0006_require_contenttypes_0002','2021-03-29 13:29:39.332947'),(9,'auth','0007_alter_validators_add_error_messages','2021-03-29 13:29:39.344173'),(10,'auth','0008_alter_user_username_max_length','2021-03-29 13:29:39.356312'),(11,'auth','0009_alter_user_last_name_max_length','2021-03-29 13:29:39.370651'),(12,'auth','0010_alter_group_name_max_length','2021-03-29 13:29:39.451747'),(13,'auth','0011_update_proxy_permissions','2021-03-29 13:29:39.469883'),(14,'auth','0012_alter_user_first_name_max_length','2021-03-29 13:29:39.483632'),(15,'users','0001_initial','2021-03-29 13:29:46.391134'),(16,'admin','0001_initial','2021-03-29 13:29:50.540938'),(17,'admin','0002_logentry_remove_auto_add','2021-03-29 13:29:50.675003'),(18,'admin','0003_logentry_add_action_flag_choices','2021-03-29 13:29:50.687257'),(19,'recipe','0001_initial','2021-03-29 13:30:03.021951'),(20,'recipe','0002_auto_20210326_1900','2021-03-29 13:30:03.477653'),(21,'recipe','0003_auto_20210327_1902','2021-03-29 13:30:03.600983'),(22,'recipe','0004_auto_20210327_1909','2021-03-29 13:30:03.648688'),(23,'recipe','0005_auto_20210327_1910','2021-03-29 13:30:03.763583'),(24,'recipe','0006_auto_20210327_1934','2021-03-29 13:30:03.831647'),(25,'sessions','0001_initial','2021-03-29 13:30:05.429039'),(26,'users','0002_auto_20210305_1833','2021-03-29 13:30:06.569745'),(27,'recipe','0007_auto_20210331_0725','2021-03-31 07:25:41.389400'),(28,'recipe','0007_auto_20210403_0740','2021-04-03 08:03:32.089908'),(29,'recipe','0008_merge_20210403_0803','2021-04-03 08:03:32.096142'),(30,'recipe','0008_auto_20210427_1902','2021-04-27 19:02:29.487385'),(31,'recipe','0009_auto_20210501_0921','2021-05-01 09:21:42.286874'),(32,'recipe','0010_auto_20210501_0942','2021-05-01 09:42:23.971129'),(33,'recipe','0011_auto_20210502_0757','2021-05-02 07:57:52.123085'),(34,'recipe','0012_remove_ingredient_type','2021-05-02 08:43:32.466854'),(35,'recipe','0013_merge_20210502_1039','2021-05-02 10:39:53.681710');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('3dzbct365ymx46y520u41zqp40ehb152','.eJxVjMsOwiAUBf-FtSEgYC8u3fsN5D5AqoYmpV0Z_12bdKHbMzPnpRKuS01rz3MaRZ2VVYffjZAfuW1A7thuk-apLfNIelP0Tru-TpKfl939O6jY67ceGODIuZBkUyALF2sKhRhEKDpwvkSMgl5O1g8WfGAHIkDAznljg3p_ABeEOHg:1lZcUS:0MDVbZA6PWBRjBy4zpI-5nDhuzfmiEV0gDzNPgQZC6U','2021-05-06 16:47:44.736424'),('8tbgd1w6bwgjgc344v0d5uftoutoofdu','.eJxVjMsOwiAUBf-FtSEgYC8u3fsN5D5AqoYmpV0Z_12bdKHbMzPnpRKuS01rz3MaRZ2VVYffjZAfuW1A7thuk-apLfNIelP0Tru-TpKfl939O6jY67ceGODIuZBkUyALF2sKhRhEKDpwvkSMgl5O1g8WfGAHIkDAznljg3p_ABeEOHg:1lRZTz:LP7foxL5kR1vKbZgojOiOx748Jjes4lD3ohSNPrFn2Q','2021-04-14 11:57:59.757692'),('8wxxpyolifejsdsc729hzrwlnp2p2sh5','.eJxVjMsOwiAUBf-FtSEgYC8u3fsN5D5AqoYmpV0Z_12bdKHbMzPnpRKuS01rz3MaRZ2VVYffjZAfuW1A7thuk-apLfNIelP0Tru-TpKfl939O6jY67ceGODIuZBkUyALF2sKhRhEKDpwvkSMgl5O1g8WfGAHIkDAznljg3p_ABeEOHg:1lcllg:PUnrg4_3_5Gf3SExguqT2NOKlFNq8ulNYR3uAKcXntA','2021-05-15 09:18:32.083054'),('e76kw7uo2wd4460cka81gmrdakfodatb','.eJxVjMsOwiAUBf-FtSEgYC8u3fsN5D5AqoYmpV0Z_12bdKHbMzPnpRKuS01rz3MaRZ2VVYffjZAfuW1A7thuk-apLfNIelP0Tru-TpKfl939O6jY67ceGODIuZBkUyALF2sKhRhEKDpwvkSMgl5O1g8WfGAHIkDAznljg3p_ABeEOHg:1lcmTM:TvN3AFUTkw_lf-gIdFC67u6zRTgRNc3vNNRkfuUFRIw','2021-05-15 10:03:40.625948'),('gu9txr9vbbwxwkp3v0zxyvf2brko0dkh','.eJxVjMsOwiAUBf-FtSEgYC8u3fsN5D5AqoYmpV0Z_12bdKHbMzPnpRKuS01rz3MaRZ2VVYffjZAfuW1A7thuk-apLfNIelP0Tru-TpKfl939O6jY67ceGODIuZBkUyALF2sKhRhEKDpwvkSMgl5O1g8WfGAHIkDAznljg3p_ABeEOHg:1lYOT2:7HzTjXmF5LwC5iPj0GP_oZStPlGr52ptsQdNxHHj5Fs','2021-05-03 07:37:12.346838'),('ouah5iaxo296lxrhrj6nvb5ycmyco3sy','.eJxVjMsOwiAUBf-FtSEgYC8u3fsN5D5AqoYmpV0Z_12bdKHbMzPnpRKuS01rz3MaRZ2VVYffjZAfuW1A7thuk-apLfNIelP0Tru-TpKfl939O6jY67ceGODIuZBkUyALF2sKhRhEKDpwvkSMgl5O1g8WfGAHIkDAznljg3p_ABeEOHg:1lRXmJ:KMem3ESYs-1-C_fyGVR80lhf-ZUzXPa-9gPzaun12UA','2021-04-14 10:08:47.652357'),('utmwxbcn0s3meq8v2e9q853mls3cy10k','.eJxVjMsOwiAUBf-FtSEgYC8u3fsN5D5AqoYmpV0Z_12bdKHbMzPnpRKuS01rz3MaRZ2VVYffjZAfuW1A7thuk-apLfNIelP0Tru-TpKfl939O6jY67ceGODIuZBkUyALF2sKhRhEKDpwvkSMgl5O1g8WfGAHIkDAznljg3p_ABeEOHg:1lSf4A:KLnCzWigpkgl5tiLNtRZaR59vTliOCEspSTJsJbC4pI','2021-04-17 12:07:50.105411'),('we26ievxfzwlc8itd08y7kmnfxbdficr','.eJxVjMsOwiAUBf-FtSEgYC8u3fsN5D5AqoYmpV0Z_12bdKHbMzPnpRKuS01rz3MaRZ2VVYffjZAfuW1A7thuk-apLfNIelP0Tru-TpKfl939O6jY67ceGODIuZBkUyALF2sKhRhEKDpwvkSMgl5O1g8WfGAHIkDAznljg3p_ABeEOHg:1lWIfk:AnnXdVhZsSpZwNlqF5kGbeR-24WKlNEnJJfwrTnOqaQ','2021-04-27 13:01:40.133161'),('yz5hnxzpg1tyq80o4954p4k15009hg9s','.eJxVjMsOwiAUBf-FtSEgYC8u3fsN5D5AqoYmpV0Z_12bdKHbMzPnpRKuS01rz3MaRZ2VVYffjZAfuW1A7thuk-apLfNIelP0Tru-TpKfl939O6jY67ceGODIuZBkUyALF2sKhRhEKDpwvkSMgl5O1g8WfGAHIkDAznljg3p_ABeEOHg:1laLo0:UovQ9Trk6DvQbhoTQgVcuoaOY4PKqFORyfy3goMNXXE','2021-05-08 17:10:56.724417');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recipe_ingredient`
--

DROP TABLE IF EXISTS `recipe_ingredient`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recipe_ingredient` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `slug` varchar(50) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `recipe_ingredient_user_id_name_a83e3f56_uniq` (`user_id`,`name`),
  KEY `recipe_ingredient_slug_acc53f84` (`slug`),
  KEY `recipe_ingredient_user_id_762a091e` (`user_id`),
  CONSTRAINT `recipe_ingredient_user_id_762a091e_fk_users_myuser_id` FOREIGN KEY (`user_id`) REFERENCES `users_myuser` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=126 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recipe_ingredient`
--

LOCK TABLES `recipe_ingredient` WRITE;
/*!40000 ALTER TABLE `recipe_ingredient` DISABLE KEYS */;
INSERT INTO `recipe_ingredient` VALUES (1,'Majonez','majonez2',1),(2,'Makaron spaghetti','makaron-spaghetti',1),(3,'Tofu mielone','tofu-mielone',1),(4,'Passata pomidorowa','passata-pomidorowa',1),(5,'Marchewka','marchewka',1),(6,'Seler naciowy','seler-naciowy',1),(7,'Cebula','cebula',1),(8,'Czosnek','czosnek',1),(9,'Oliwa z oliwek','oliwa-z-oliwek',1),(10,'Wino czerwone','wino-czerwone',1),(11,'Sól','sol',1),(12,'Pieprz','pieprz',1),(13,'Bulion warzywny','bulion-warzywny',1),(14,'Świeża bazylia','swieza-bazylia',1),(15,'Parmezan (wegański)','parmezan-weganski',1),(16,'Tofu','tofu',1),(17,'Płatki drożdżowe','patki-drozdzowe',1),(18,'Sos sojowy','sos-sojowy',1),(19,'Czosnek w proszku','czosnek-w-proszku',1),(20,'Cebula w proszku','cebula-w-proszku',1),(21,'Olej roślinny','olej-roslinny',1),(22,'Papryka słodka wędzona','papryka-sodka-wedzona',1),(23,'Kasza jęczmienna pęczak','kasza-jeczmienna-peczak',1),(24,'Jarmuż','jarmuz',1),(25,'Olej','olej',1),(26,'Bataty','bataty',1),(27,'Papryka','papryka',1),(28,'Cebula czerwona','cebula-czerwona',1),(29,'Kurkuma','kurkuma',1),(30,'Słodka papryka','sodka-papryka',1),(31,'Kmin rzymski','kmin-rzymski',1),(32,'Papryczka chili','papryczka-chili2',1),(33,'Feta','feta',1),(34,'Schab','schab',1),(35,'Bulion','bulion',1),(36,'mąki','maki',1),(37,'ziemniaki','ziemniaki',1),(38,'masło','maso',1),(39,'śmietana 18%','smietana-18',1),(40,'Koperek świeży posiekany','koperek-swiezy-posiekany',1),(41,'Natka pietruszki świeża posiekana','natka-pietruszki-swieza-posiekana',1),(42,'Czerwone buraki (ugotowane)','czerwone-buraki-ugotowane',1),(43,'mleko','mleko',1),(44,'mąka pszenna','maka-pszenna',1),(45,'cukier','cukier',1),(46,'sok z cytryny','sok-z-cytryny',1),(47,'Czerwona soczewica','czerwona-soczewica',1),(48,'Zielona soczewica','zielona-soczewica',1),(49,'Krojone pomidory z puszki','krojone-pomidory-z-puszki',1),(50,'Garam masala','garam-masala',1),(51,'Curry','curry',1),(52,'chili w proszku','chili-w-proszku',1),(53,'sól morska','sol-morska',1),(54,'jogurt','jogurt',1),(55,'Kasza bulgur','kasza-bulgur',1),(56,'Marchewka z groszkiem','marchewka-z-groszkiem',1),(57,'polędwiczki z dorsza','poledwiczki-z-dorsza',1),(58,'Sól, pieprz','sol-pieprz',1),(59,'Filety z kurczaka','filety-z-kurczaka',1),(60,'Cukinia','cukinia',1),(61,'Czerwona papryka','czerwona-papryka',1),(62,'Żółta papryka','zota-papryka',1),(63,'suszone oregano','suszone-oregano',1),(64,'Koncentrat pomidorowy','koncentrat-pomidorowy',1),(65,'mąka ziemniaczana','maka-ziemniaczana',1),(66,'pomidorki koktajlowe','pomidorki-koktajlowe',1),(67,'ciepła woda','ciepa-woda',1),(68,'drożdże instant','drozdze-instant',1),(69,'Zioła prowansalskie','zioa-prowansalskie',1),(70,'Kasza jaglana','kasza-jaglana',1),(71,'mąka z ciecierzycy','maka-z-ciecierzycy',1),(72,'jajko','jajko',1),(73,'natka pietruszki','natka-pietruszki',1),(74,'olej rzepakowy','olej-rzepakowy',1),(75,'Pietruszka (korzeń)','pietruszka-korzen',1),(76,'bułka tarta','buka-tarta',1),(77,'papryka ostra','papryka-ostra',1),(78,'śmietana 30% słodka','smietana-30-sodka',1),(79,'Kukurydza','kukurydza',1),(80,'Czerwona fasola','czerwona-fasola',1),(81,'Biała fasola','biaa-fasola',1),(82,'Kostka rosołowa','kostka-rosoowa',1),(83,'przyprawa do potraw meksykańskich','przyprawa-do-potraw-meksykanskich',1),(84,'liść laurowy','lisc-laurowy',1),(85,'ziele angielskie','ziele-angielskie',1),(86,'majeranek','majeranek',1),(87,'szpinak świeży','szpinak-swiezy',1),(88,'rzodkiewka','rzodkiewka',1),(89,'szczypiorek','szczypiorek',1),(90,'Ostra musztarda','ostra-musztarda',1),(91,'Cebula dymka','cebula-dymka',1),(92,'musztarda','musztarda',1),(93,'ocet winny biały','ocet-winny-biay',1),(94,'mleko 2%','mleko-2',1),(95,'wanilia','wanilia',1),(96,'orzeszki ziemne','orzeszki-ziemne',1),(97,'ksylitol','ksylitol',1),(98,'Suszone daktyle','suszone-daktyle',1),(99,'masło orzechowe','maso-orzechowe',1),(100,'syrop klonowy','syrop-klonowy',1),(101,'czekolada gorzka','czekolada-gorzka',1),(102,'proszek do pieczenia','proszek-do-pieczenia',1),(103,'cukier puder','cukier-puder',1),(104,'kakao','kakao',1),(105,'dżem z czarnej porzeczki','dzem-z-czarnej-porzeczki',1),(106,'drożdże','drozdze',1),(107,'cukier waniliowy','cukier-waniliowy',1),(108,'wiśnie','wisnie',1),(110,'Orzechy nerkowca','orzechy-nerkowca',1),(111,'Makaron penne','makaron-penne',1),(112,'Szparagi','szparagi',1),(113,'Ryż czerwony','ryz-czerwony',1),(114,'Ryż czarny','ryz-czarny',1),(115,'Orkisz','orkisz',1),(116,'Zalewa z papryki','zalewa-z-papryki',1),(117,'Suszone pomidory (przyprawa)','suszone-pomidory-przyprawa',1),(118,'przyprawa do kurczaka','przyprawa-do-kurczaka',1),(119,'Harisa','harisa',1),(120,'woda','woda',1);
/*!40000 ALTER TABLE `recipe_ingredient` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recipe_ingredient_tag`
--

DROP TABLE IF EXISTS `recipe_ingredient_tag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recipe_ingredient_tag` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ingredient_id` int NOT NULL,
  `tag_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `recipe_ingredient_tag_ingredient_id_tag_id_c52490b8_uniq` (`ingredient_id`,`tag_id`),
  KEY `recipe_ingredient_tag_tag_id_e63b3b33_fk_recipe_tag_id` (`tag_id`),
  CONSTRAINT `recipe_ingredient_ta_ingredient_id_a6bbb15c_fk_recipe_in` FOREIGN KEY (`ingredient_id`) REFERENCES `recipe_ingredient` (`id`),
  CONSTRAINT `recipe_ingredient_tag_tag_id_e63b3b33_fk_recipe_tag_id` FOREIGN KEY (`tag_id`) REFERENCES `recipe_tag` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recipe_ingredient_tag`
--

LOCK TABLES `recipe_ingredient_tag` WRITE;
/*!40000 ALTER TABLE `recipe_ingredient_tag` DISABLE KEYS */;
/*!40000 ALTER TABLE `recipe_ingredient_tag` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recipe_recipe`
--

DROP TABLE IF EXISTS `recipe_recipe`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recipe_recipe` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `calories` int DEFAULT NULL,
  `prepare_time` int DEFAULT NULL,
  `last_cook_date` date NOT NULL,
  `slug` varchar(50) NOT NULL,
  `photo1` varchar(100) NOT NULL,
  `photo2` varchar(100) NOT NULL,
  `photo3` varchar(100) NOT NULL,
  `difficulty` varchar(1) NOT NULL,
  `description` longtext NOT NULL,
  `user_id` int NOT NULL,
  `portions` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `recipe_recipe_user_id_slug_208c5a8e_uniq` (`user_id`,`slug`),
  KEY `recipe_recipe_slug_49f84e76` (`slug`),
  CONSTRAINT `recipe_recipe_user_id_3eb7547f_fk_users_myuser_id` FOREIGN KEY (`user_id`) REFERENCES `users_myuser` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recipe_recipe`
--

LOCK TABLES `recipe_recipe` WRITE;
/*!40000 ALTER TABLE `recipe_recipe` DISABLE KEYS */;
INSERT INTO `recipe_recipe` VALUES (2,'Spaghetti tofu bolognese',0,0,'2021-04-03','spaghetti-tofu-bolognese','','','','S','<p><b>Składniki na 4 porcje</b></p><p>1.	Przygotuj tofu mielone zgodnie z tym przepisem (następna strona). Jeśli nie masz czasu, nie musisz go piec: wystarczy dobrze podsmażyć na patelni lub w rondlu.</p><p>2.	Na rozgrzanej patelni z oliwą z oliwek podsmaż czosnek i cebulę, aż się zeszklą. Przełóż je na mały spodeczek lub do miseczki. Na patelni podsmaż bardzo drobno pokrojoną marchewkę i łodygę selera – możesz wspomagać się bulionem warzywnym, aby nic się nie przypaliło.</p><p>3.	Dodaj posiekane grzyby i zalej winem: duś do odparowania alkoholu.</p><p>4.	Na patelnię przelej passatę pomidorową, dodaj czosnek i cebulę i dopraw gałką muszkatołową, solą i pieprzem. Dodaj wcześniej przygotowane tofu. Duś na powolnym ogniu, aż woda odparuje.</p><p>5.	W głębokim garnku z wrzątkiem ugotuj makaron zgodnie z zaleceniami na opakowaniu. Odcedź i rozłóż na talerze lub dodaj na patelnię z sosem i wymieszaj (wersja mniej oficjalna).</p><p>6.	Na makaron nakładaj porcje sosu bolognese z dodatkiem posiekanej bazylii i wegeparmezanu.</p><p>7.	Smacznego! Odgrzane na drugi dzień smakuje równie pysznie.</p><p><br></p>',1,NULL),(3,'Zamiast mięsa - mielone tofu',0,0,'2021-03-31','zamiast-miesa-mielone-tofu','','','','S','<p>1 blacha</p><p>1. Piekarnik nagrzej na 200ºC z funkcją termoobiegu.</p><p>2.	Do szerokiej miski przełóż odsączone tofu i rozgnieć je widelcem bądź rękoma na mniejsze kawałki – nie potrzeba do tego maszynki do mielenia </p><p>3.	W małej szklance wymieszaj wszystkie sypkie przyprawy i dodaj je do rozkruszonego tofu. Kolejno dodaj sos sojowy i wszystko dokładnie wymieszaj. Dopraw pieprzem i ew. solą – jednak uwaga, by nie przesolić – gdyż sos sojowy jest sam z siebie bardzo słony.</p><p>4.	Tofu podsmaż na mocno rozgrzanej patelni z olejem roślinnym, nie mieszaj – pozwól mu się lekko przypalić. Pamiętaj, aby używać patelni z nieprzywierającą powłoką. Jeżeli nie masz czasu lub masz po prostu lenia, punkt z patelnią możesz pominąć.</p><p>5.	Na wyłożonej papierem do pieczenia blasze wyłóż tofu równomiernie i płasko. Gdy włożysz je do piekarnika zmniejsz temperaturę do 150ºC i piecz tofu przez około 10 minut, cały czas zerkając, czy się nie przypala.</p><p>6.	Co kilka minut przemieszaj je i włóż z powrotem do pieczenia. Czynność powtarzaj, aż uzyskasz pożądaną przez Ciebie suchość/miękkość tofu. Mnie zajmuje to zazwyczaj do 20 minut – pilnuj go jednak, aby się nie spaliło!</p><p>7.	 Tak przygotowane tofu możesz używać gdzie tylko dusza zapragnie, jednak pośpiesz się, bo pewnie i tak zjesz połowę podczas gotowania. Smacznego!</p>',1,NULL),(4,'Pęczak smażony z batatami, papryką, jarmużem i fetą',0,60,'2021-04-08','peczak-smazony-z-batatami-papryka-jarmuzem-i-feta','','','','S','<p>1. Pęczak wsypać do garnka, wlać 2½ szklanki bulionu lub osolonej wody, zagotować.</p><p>2. Gotować pod przykryciem na minimalnym ogniu przez 25 minut (na ostatnie pięć minut na wierzch kaszy wsypać liście jarmużu i dalej gotować pod przykryciem).<br></p><p>3.	Na patelni na oleju podsmażyć (przez ok. 10 min) pokrojonego w małą kostkę batata, paprykę oraz posiekaną czerwoną cebulę. </p><p>4.	Pod koniec dodać starty czosnek oraz przyprawy (mieloną kurkumę, słodką paprykę i kmin rzymski).</p><p>5.	Do podsmażonych warzyw dodać ugotowaną kaszę i smażyć co chwilę mieszając przez ok. 2 minuty, doprawić solą i pieprzem. </p><p>6.	Odstawić z ognia, dodać posiekane chili, posypać fetą i skropić oliwą.</p>',1,4),(5,'Schab w sosie własnym z cebulką',0,0,'2021-03-31','schab-w-sosie-wasnym-z-cebulka','','','','S','<blockquote><b>Składniki na 6 porcji</b></blockquote><p>1.Obrane cebule pokrój na półplastry o grubości około 1 cm i podsmaż na patelni z odrobiną soli na dużym ogniu cały czas mieszając, aż zacznie się szklić i miejscami nawet przypalać.</p><p>2.	Umyte i osuszone mięso pokrój na plastry o grubości około 2 cm, dopraw solą i pieprzem.</p><p>3.	Plastry schabu obsyp mąką.</p><p>4.	Na dużej patelni silnie rozgrzej 4 łyżki oleju. Włóż mięso i smaż na sporym ogniu przez 2-3 minuty z każdej strony, aż mięso całkowicie zmieni kolor i zacznie się mocno rumienić na brzegach.</p><p>5.	Mięso przełóż do dużej formy żaroodpornej.</p><p>6.	Podsmażoną cebulę ułóż pomiędzy kawałkami mięsa. Wlej bulion (tyle, by przykrył mięso). Naczynie przykryj folią aluminiową (ale niezbyt dokładnie, by płyn mógł parować).</p><p>7.	Naczynie ze schabem wstaw do piekarnika nagrzanego do 180 stopni i zapiekaj przez 2 godziny - aż mięso będzie mięciutkie. Po tym czasie zdejmij folię i trzymaj mięso w gorącym piekarniku przez 15 minut, by ładnie się przyrumieniło na wierzchu.</p>',1,NULL),(6,'Puree z ziemniaków',0,0,'2021-03-31','puree-z-ziemniakow','','','','S','<p>1.	Ziemniaki obierz, umyj i ugotuj do miękkości w osolonej wodzie. Ugotowane odcedź i odparuj. Pozostaw na małym gazie (lub najmniejszej temperaturze płyty).</p><p>2.	Do ziemniaków wrzuć masło i wlej śmietankę, lekko podgrzej, żeby dodatki nie ochłodziły ziemniaków.</p><p>3.	Ziemniaki rozgnieć dokładnie tłuczkiem, a jeszcze lepiej przepuść przez praskę.</p><p>4.	Dodaj posiekany koperek i natkę pietruszki. Wymieszaj, dosól do smaku.</p><p>5.	Podawaj posypane koperkiem.</p>',1,NULL),(7,'Buraczki zasmażane',0,0,'2021-05-01','buraczki-zasmazane','','','','S','<p>1.	Buraki w skórce zalać wodą do przykrycia w garnku z pokrywką i gotować do miękkości (ok. 1 godzina).</p><p>2.	Ugotowane buraki obrać, zetrzeć na tarce o dużych oczkach i wrzucić na patelnię. </p><p>3.	Posolić, popieprzyć, wlać mleko, wymieszać. </p><p>4.	Dodać pół łyżki mąki i gotować na małym ogniu, od czasu do czasu mieszając. </p><p>5.	Kiedy trochę zgęstnieją dodać cukier i sok z cytryny.</p><p>6.	Na końcu dodać masło i mieszać, aż do rozpuszczenia masła.</p>',1,NULL),(8,'Wegetariański gulasz z soczewicy',0,0,'2021-03-31','wegetarianski-gulasz-z-soczewicy','','','','S','<p>1.	Cebule i seler naciowy pokroić w kostkę. </p><p>2.	W rondlu rozgrzać oliwę z oliwek, zeszklić cebulę, dodać seler naciowy i chwilę poddusić. </p><p>3.	Wrzucić drobno posikany czosnek i papryczkę chili, kurkumę, curry, oraz garam masalę - stale mieszając podsmażać przez minutę. </p><p>4.	Dosypać oba rodzaje soczewicy (opłukane), zamieszać i dodać pomidory. </p><p>5.	Wlać litr wody, doprawić solą i pieprzem. </p><p>6.	Zagotować i dusić na małym ogniu ok. 30 minut, co jakiś czas mieszając. </p><p>7.	Może to potrwać nieco dłużej, w razie gdyby potrawa zrobiła się zbyt gęsta podlać wodą. </p><p>8.	Gdy soczewica będzie miękka, a gulasz odpowiednio gęsty – skropić go sokiem z cytryny, doprawić jeszcze solą i pieprzem do smaku.  </p><p>9.	Gotowy nalewamy do miseczek i podajemy z jogurtem lub śmietaną.</p>',1,NULL),(9,'Dorsz w sosie curry z marchewką i groszkiem',0,0,'2021-03-31','dorsz-w-sosie-curry-z-marchewka-i-groszkiem','','','','S','<p>1.	Nastawić kaszę bulgur - ugotować w osolonej wodzie, zwykle ok. 15 minut lub zgodnie z instrukcją na opakowaniu.</p><p>2.	Do garnka włożyć 2 łyżki masła oraz przyprawę curry. Mrożoną marchewkę z groszkiem wsypać na sitko i przepłukać pod ciepłą wodą. Wrzucić do garnka z masłem i mieszając podgrzewać przez ok. 5 minut aż warzywa się rozmrożą.</p><p>3.	Wlać bulion, w razie potrzeby doprawić solą i pieprzem i gotować przez ok. 5 minut do miękkości warzyw. Wlać śmietankę i gotować jeszcze 2 minuty.</p><p>4.	Filety dorsza dokładnie rozmrozić i dokładnie osuszyć papierowymi ręcznikami. Doprawić solą, pieprzem i obtoczyć w mące pszennej.</p><p>5.	Rozgrzać dużą patelnię z kilkoma łyżkami oliwy. Włożyć filety i smażyć przez 4 minuty, przewrócić na drugą stronę i smażyć przez kolejne 3 minuty.</p><p>6.	Dodać marchewkę z groszkiem z garnka wraz z całym sosem, potrząsnąć patelnią rozprowadzając sos pomiędzy kawałki ryby i gotować przez ok. 3 minuty.</p><p>7.	Posypać natką i podawać na ugotowanej kaszy bulgur.</p>',1,NULL),(10,'Kurczak z warzywami',0,0,'2021-03-31','kurczak-z-warzywami','','','','S','<p>1.	Filety oczyścić z kostek i błonek, pokroić wzdłuż na mniejsze porcje (każdy filet na 3 części). Doprawić solą i pieprzem.</p><p>2.	Cukinię i papryki pokroić w kostkę. Cebulę w piórka. Czosnek obrać i zetrzeć.</p><p>3.	W większym garnku na łyżce oliwy poddusić cebulę, następnie dodać cukinię i papryki. Smażyć co chwilę mieszając przez ok. 5 minut. Odłożyć na talerz.</p><p>4.	Do tego samego garnka wlać dodatkową łyżkę oliwy i obsmażyć kurczaka z każdej strony, w sumie przez ok. 8 minut.</p><p>5.	Dodać masło, starty czosnek oraz odłożone warzywa. Doprawić solą, pieprzem, oregano i ostrą papryczką. Wymieszać i podgrzać.</p><p>6.	Wlać gorący bulion i zagotować. Przykryć i dusić przez ok. 15 minut aż mięso będzie miękkie i będzie się cząstkować.</p><p>7.	Pod koniec dodać pokrojone pomidorki koktajlowe jeśli ich używamy oraz natkę i koncentrat pomidorowy.</p><p>8.	Zagęścić obydwiema mąkami wsypywanymi do wywaru bezpośrednio przez sitko. Wymieszać i pogotować jeszcze 1 minutę.</p>',1,NULL),(11,'Pizza - ciasto',0,0,'2021-03-31','pizza-ciasto','','','','S','<p>1.	Do dużej miski wsypałem mąkę, drożdże i dobrze wymieszałem.</p><p>2.	Następnie dodałem olej, cukier, sól i znowu wszystko dobrze wymieszałem.</p><p>3.	Zacząłem stopniowo dolewać wodę i łyżką, a pod koniec już ręką wyrabiałem ciasto aż powstała jednolita kula (jeżeli ciasto się lepi to dodaj mąki i dalej wyrabiaj).</p><p>4.	Ciasto powinno trochę urosnąć, dlatego uformowaną kulę ciasta zostawiłem w ciepłym miejscu w przykrytej misce na 20-30 minut.</p><p>5.	Kiedy ciasto odpoczywało, przygotowałem składniki, które zamierzałem ułożyć na pizzy.</p><p>6.	Ciasto najpierw rozgniotłem dłońmi na gruby placek, a następnie porozciągałem. W ten sposób uformowała się ładna okrągła pizza, którą ułożyłem na posmarowanej odrobiną oleju blasze i jeszcze dłońmi rozprowadziłem placek tak, żeby zajmował całą formę (technika doprowadzania pizzy do kształtu blachy jest dowolna).</p><p>7.	Na ciasto nałożyłem sos pomidorowy i kilka rzeczy zalegających w lodówce (salami, oliwki, cebula pocięta w piórka).</p><p>8.	Tak przygotowana pizza wylądowała w piekarniku nagrzanym uprzednio do temperatury 220 stopni celsjusza.</p><p>9.	Każdy powinien znać swój piekarnik i dostosować indywidualnie czas pieczenia. </p><p>- Bardziej wprawionym osobom polecam pieczenie pizzy w maksymalnej temperaturze na samym dnie piekarnika. Dzięki temu pizza nawet w domowych warunkach jest upieczona w około 7-8 minut.</p><p>&nbsp;Na blaszce na kratce na dnie piekarnika: ___ minut w maksymalnej temperaturze.</p>',1,NULL),(12,'Kotlety z cukinii i kaszy jaglanej',0,0,'2021-03-31','kotlety-z-cukinii-i-kaszy-jaglanej','','','','S','<p>1.	Kaszę jaglaną ugotuj do miękkości według zaleceń producenta.</p><p>2.	Cukinię i marchew zetrzyj na tarce na grubych oczkach, posiekaj cebulę, natkę kolendry, chili i czosnek. Wyciśnij sok z połówki cytryny.</p><p>3.	Cukinię oprósz łyżką soli i odstaw na bok na 30 minut - jak puści sok odciśnij i wypłucz.</p><p>4.	W małej misce połącz jogurt, sok z cytryny, połowę czosnku.</p><p>5.	W kolejnej misce połącz ugotowaną kaszę, mąkę z ciecierzycy, marchew, cebulę, cukinię, chili, pozostałą połowę czosnku i połowę natki kolendry. Dodaj jajko, masę dopraw kminem - powinna być dość plastyczna.</p><p>6.	Uformuj z niej małe okrągłe kotleciki i smaż na oleju na średnio rozgrzanej patelni po około 2 minuty z każdej strony, aż zrobią się złociste. Podawaj z sosem jogurtowo-czosnkowym i pozostałą natką kolendry.</p>',1,NULL),(13,'Klopsiki z kaszy jaglanej w sosie pomidorowym',0,0,'2021-04-19','klopsiki-z-kaszy-jaglanej-w-sosie-pomidorowym','recipes/Patryk/klopsiki-z-kaszy-jaglanej-w-sosie-pomidorowym/f7fcfff3-8491-4e4d-8a6c-547_JJSgUvE.jpg','','','S','<p>1.	Aby przygotować sos pomidorowy, posiekaj cebulę i czosnek. Przysmaż na oliwie, dodaj passatę, gotuj na małym ogniu przez 20 – 25 minut, aż sos zgęstnieje, dopraw do smaku.</p><p>2.	Kaszę jaglaną przepłucz dwukrotnie na sicie, użyj gorącej wody.</p><p>3.	Następnie kaszę przełóż do garnka, dodaj 3 szklanki gorącej wody, szczyptę soli,, gotuj pod przykryciem na małym ogniu około 10 – 15 minut.</p><p>4.	Cebulę posiekaj, marchew, pietruszkę zetrzyj na tarce. Warzywa przysmaż na oliwie, dodaj oregano i curry, duś około 20 minut.</p><p>5.	W robocie kuchennym wymieszaj i zblenduj kaszę z warzywami, bułką tartą, dodaj sól i pieprz. Jeśli nie chcesz mieć jednolitej papki, kawałki warzyw powinny być widoczne, więc miksuj tylko chwilę. Masa powinna być kleista, sprawdź także, czy jest dobrze doprawiona.</p><p>6.	Z masy lep małe klopsiki wielkości orzecha włoskiego.</p><p>7.	Klopsiki smaż przez kilka minut na patelni.</p><p>8.	Sos pomidorowy przelej do naczynia żaroodpornego, do sosu wrzuć klopsiki, zapiekaj około 20 minut w 180 stopniach.</p><p>9.	Przed podaniem dodaj pietruszkę i tarty parmezan.</p>',1,4),(14,'Zupa z soczewicą i pomidorami',0,0,'2021-03-31','zupa-z-soczewica-i-pomidorami','','','','S','<p>1.	W garnku na oliwie zeszklić pokrojoną w kosteczkę cebulę. </p><p>2.	Dodać przeciśnięty przez praskę czosnek i mieszając smażyć jeszcze przez minutę. </p><p>3.	Dodać suchą soczewicę, przyprawy i wymieszać.</p><p>4.	Wlać bulion i zagotować. </p><p>5.	Przykryć i gotować do miękkości soczewicy przez ok. 15 - 20 minut.</p><p>6.	Dodać obrane i pokrojone w kostkę pomidory (wraz z sokiem i nasionami) lub krojone pomidory z puszki i gotować przez ok. 15 minut pod uchyloną pokrywą, od czasu do czasu zamieszać.</p><p>7.	W międzyczasie w razie potrzeby doprawić solą i pieprzem. </p><p>8.	Odstawić z ognia i wymieszać ze śmietanką oraz posiekaną zieleniną.</p>',1,NULL),(15,'Zupa meksykańska',0,0,'2021-03-31','zupa-meksykanska','','','','S','<p>1.	Do dużego garnka wlewamy zawartość wszystkich puszek, wraz z zalewami. Kukurydzę, czerwoną i białą fasolę, oraz pomidory, umieszczamy zatem w garnku bez odcedzania.</p><p>2.	Do warzyw dolewamy około 0,75 litra wody, a następnie dodajemy pokruszone kostki rosołowe, ziele angielskie, liść laurowy, sól i pieprz oraz pół opakowania słodkiej papryki. Wszystko gotujemy na małym ogniu.</p><p>3.	Mięso mielone smażymy na patelni wraz z całą przyprawą do potraw meksykańskich oraz posiekaną cebulą.</p><p>4.	Po kilku minutach, do mięsa dodajemy także posiekaną paprykę i smażymy do momentu, aż warzywa będą miękkie.</p><p>5.	Na koniec, na patelnię wsypujemy drugą połowę mielonej papryki, zioła prowansalskie i bazylię. Wszystko dokładnie mieszamy i przekładamy do garnka z gotującymi się składnikami.</p><p>6.	Na patelnię wlewamy szklankę wody, do której dodajemy koncentrat pomidorowy i zmiażdżony czosnek. Kiedy woda się zagotuje, przelewamy wszystko do garnka.</p><p>7.	Wszystko dokładnie ze sobą mieszamy i doprawiamy do smaku solą oraz pieprzem.</p>',1,NULL),(16,'Toskańska zupa z fasolą i cukinią',0,0,'2021-03-31','toskanska-zupa-z-fasola-i-cukinia','','','','S','<p>1.	W garnku na oliwie poddusić pokrojoną w kosteczkę cebulę. Dodać obraną i pokrojoną w kosteczkę marchewkę i smażyć podsmażać przez ok. 5 minut.</p><p>2.	Dodać obrany i starty czosnek, wymieszać, chwilę podsmażyć. Wlać gorący bulion i zagotować.</p><p>3.	Dodać całą zawartość puszki (fasolka + zalewa) oraz krojone pomidory z puszki (można je zmiksować), koncentrat, oregano, majeranek. Doprawić solą i pieprzem. Zagotować, przykryć i gotować pod przykryciem przez ok. 10 minut.</p><p>4.	Dodać pokrojoną w kostkę cukinię i gotować przez kolejne 10 minut. Na minutę przed końcem dodać opłukany szpinak. Podawać z tartym parmezanem i bazylią.</p>',1,NULL),(17,'Pasta jajeczna',0,0,'2021-03-31','pasta-jajeczna','','','','S','<p>1.	Jajka włóż do garnka z zimną wodą, ustaw na małym ogniu. Od momentu, aż woda zacznie się gotować, licz 10 minut, wtedy jajka są gotowe.</p><p>2.	Odlej z garnka wrzątek i przelej jajka zimną wodą.</p><p>3.	Gdy się ostudzą, obierz je i zetrzyj na tarce o grubych oczkach (możesz też drobno posiekać).</p><p>4.	Jajka wymieszaj w misce z majonezem, posiekanym szczypiorkiem, śmietaną, musztardą. Dodaj sól i świeżo mielony pieprz oraz posiekaną cebulkę.</p><p>5.	Pastę wyłóż na kromki świeżego chleba, na wierzchu ułóż plasterki rzodkiewki!</p>',1,NULL),(18,'Majonez domowy',0,0,'2021-03-31','majonez-domowy','','','','S','<p>1.	Jajko wbij do miski, dodaj sól, pieprz oraz ocet i musztardę. </p><p>2.	Miksuj składniki na bardzo niskich obrotach, powoli je zwiększając. </p><p>3.	Wolnym strumieniem wlewaj do miski olej. </p><p>4.	Zwróć uwagę na to, że im więcej oleju dodasz, tym gęstszy będzie majonez. </p><p>5.	Gdy masa uzyska pożądaną gęstość i konsystencję, przełóż majonez do miseczki lub słoika. </p><p>6.	Pamiętaj, że należy go zjeść jak najszybciej. </p><p>7.	Domowy majonez nie zawiera konserwantów, więc psuje się znacznie szybciej niż majonez ze sklepu.</p>',1,NULL),(19,'Deser jaglany a\'la Snickers',0,0,'2021-03-31','deser-jaglany-ala-snickers','','','','S','<p>1.	Kaszę jaglaną podpraż na suchej patelni, aż poczujesz orzechowy aromat. W rondelku zagotuj mleko z dodatkiem laski wanilii. Do gotującego się mleka wsyp kaszę i gotuj przez ok. 15 minut. Daktyle zalej wrzątkiem i odstaw na czas gotowania się kaszy.</p><p>2.	Odsączone daktyle przełóż do misy blendera i zmiksuj na pastę. Dodaj masło orzechowe, syrop klonowy i mieszaj do momentu połączenia się składników. Gotowy sos przełóż do miseczki.</p><p>3.	Do misy blendera przelej całą zawartość garnka. Dodaj ksylitol i zblenduj na gładki krem. W razie potrzeby dolej więcej mleka. Orzeszki ziemne posiekaj, a czekoladę rozpuść z dodatkiem mleka i ksylitolu w kąpieli wodnej.</p><p>4.	Porcję kremu jaglanego przełóż do słoiczka. Posyp go orzeszkami ziemnymi i polej sosem daktylowo – orzechowym. Wyłóż kolejną porcję kremu, orzeszki ziemne i sos. Gotowy deser polej czekoladą.</p>',1,NULL),(20,'Pleśniak z dżemem porzeczkowym',0,0,'2021-03-31','plesniak-z-dzemem-porzeczkowym','','','','S','<p>1.	Mąkę wsypujemy do miski, dodajemy proszek do pieczenia, 3 łyżki cukru oraz sól – mieszamy.</p><p>2.	Zimne masło drobno siekamy do miski z mąką, szybko mieszamy.</p><p>3.	Białka oddzielamy od żółtek, żółtka dodajemy do miski z ciastem, zagniatamy ciasto, dzielimy na 3 części, do jednej dodajmy kakao, chłodzimy w lodówce przez co najmniej godzinę.</p><p>4.	Blachę wykładamy papierem do pieczenia, ścieramy na tarce jedno jasne ciasto, wykładamy dżem z czarnej porzeczki, przykrywamy startym ciastem kakaowym.</p><p>5.	Białka ubijamy na sztywno dodając pod koniec cukier puder i mąkę ziemniaczaną, wykładamy na stare kakaowe ciasto i przykrywamy ostatnim jasnym ciastem.</p><p>6.	Wkładamy do nagrzanego na 180C piekarnika na ok. 40-45 minut.</p>',1,NULL),(21,'Bułeczki drożdżowe z wiśniami',0,0,'2021-03-31','bueczki-drozdzowe-z-wisniami','','','','S','<p>1.	Mleko podgrzewamy, a następnie odlewamy większość do innego kubka, ponieważ ta niewielka ilość potrzebna jest do rozpuszczenia drożdży, wraz z łyżeczką cukru. 80 g masła rozpuszczamy i studzimy.</p><p>2.	Do miski wsypujemy pół kilo mąki pszennej. Dodajemy cukier waniliowy, łyżeczkę cukru, szczyptę soli i mieszamy. Następnie robimy w mące wgłębienie, w to wlewamy rozpuszczone drożdże, przysypujemy lekko mąką i czekamy, aż drożdże wyrosną ponad mąkę. Gdy już wyrosną, przemieszamy, dodajemy 2 jajka, rozpuszczone masło, mleko, mieszamy i zagniatamy ciasto ok. 10 min.</p><p>3.	Zagniecionym ciastem uderzamy trzy razy o stół, następnie kulę z ciasta wkładamy do miski, przykrywamy ściereczką i odstawiamy w ciepłe miejsce na ok. 1 godzinę. Musi podwoić swoją objętość.</p><p>4.	Po wyrośnięciu ciasto przekładamy na blat, chwilę zagniatamy, następnie formujemy wałeczek, który dzielimy na 10 części. Każdą część jeszcze chwilę w rękach zagniatamy, następnie rozpłaszczamy, na środek nakładamy po łyżeczce nadzienia, zbieramy brzegi, sklejamy i naprężamy wierzch bułeczki. Układamy na blasze wyłożonej papierem do pieczenia łączeniem od spodu.</p><p>5.	Bułeczki na blasze przykrywamy ściereczką i odstawiamy do napuszenia na 15-20 minut.</p><p>6.	Nagrzewamy piekarnik do temperatury 180 stopni C (wszystko zależy od piekarnika, ewentualnie należy piec w temperaturze 190 stopni C).</p><p>7.	Bułeczki, tuż przed włożeniem do piekarnika, smarujemy roztrzepanym jajkiem. Wkładamy do nagrzanego piekarnika na środkową półkę i pieczemy z grzaniem góra-dół przez 20-25 minut. Mają upiec się na złoto-brązowy kolor. Smacznego!</p>',1,NULL),(22,'Makaron w obłędnie kremowym sosie paprykowym',0,40,'2021-04-13','makaron-w-obednie-kremowym-sosie-paprykowym','recipes/Patryk/makaron-w-obednie-kremowym-sosie-paprykowym/800b7ec1-bc8a-4689-99fe-9d2666f3f32b.jpeg','','','L','<p>Paprykę myjemy i układamy na blaszce w nagrzanym do 200 stopni piekarniku. Pieczemy 50 minut. Następnie wkładamy do siatki lub do miski, którą przykrywamy talerzem. Po 10 minutach możemy zdjąć skórkę bez problemu&nbsp;</p><p>Orzechy zalewamy letnią wodą.</p><p>Na patelni rozgrzewamy olej, dodajemy pokrojoną w kostkę cebulę i czosnek, smażymy na złoto. Następnie dodajemy przyprawy i passate. Podsmażamy jeszcze 5 minut, a następnie przekładamy do kielicha blendera, dodajemy obraną i pozbawioną nasion paprykę. Wrzucamy odsączone z wody nerkowce, sok z cytryny i płatki drożdżowe oraz 50 ml wody. Blendujemy przez 60 sekund.</p><p>Na patelnie wylewamy sos, dodajemy makaron i w razie potrzeby delikatnie wlewamy do 30 ml wody. Podsmażamy razem przez 5-10 min, często mieszając. Przekładamy do miseczek i posypujemy posiekaną natką pietruszki oraz serem.</p><p>Pyszotto!! &lt;3</p>',1,4),(23,'Ryż kolorowy z warzywami i szparagami',0,90,'2021-04-20','ryz-kolorowy-z-warzywami-i-szparagami','recipes/Patryk/ryz-kolorowy-z-warzywami-i-szparagami/5624f08d-a035-4364-9f9b-ff000320cdd0.jpg','','','S','<p>Klaudia wie jak zrobić&nbsp;</p>',1,4),(24,'Sałatka #1',1,0,'2021-05-01','saatka-1','recipes/Patryk/saatka-1/e6f0377a-67e0-47c3-acf2-271f6f568e0f.jpeg','','','S','<p>Soja pieczona w oliwie z przyprawami&nbsp;</p><p>Cukinia grillowana&nbsp;</p>',1,4),(34,'test',0,0,'2021-05-02','test','','','','S','',1,NULL);
/*!40000 ALTER TABLE `recipe_recipe` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recipe_recipe_ingredient`
--

DROP TABLE IF EXISTS `recipe_recipe_ingredient`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recipe_recipe_ingredient` (
  `id` int NOT NULL AUTO_INCREMENT,
  `quantity` varchar(25) NOT NULL,
  `ingredient_id` int NOT NULL,
  `recipe_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `recipe_recipe_ingred_ingredient_id_97b2fe3b_fk_recipe_in` (`ingredient_id`),
  KEY `recipe_recipe_ingredient_recipe_id_7b8a0bd6_fk_recipe_recipe_id` (`recipe_id`),
  CONSTRAINT `recipe_recipe_ingred_ingredient_id_97b2fe3b_fk_recipe_in` FOREIGN KEY (`ingredient_id`) REFERENCES `recipe_ingredient` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `recipe_recipe_ingredient_recipe_id_7b8a0bd6_fk_recipe_recipe_id` FOREIGN KEY (`recipe_id`) REFERENCES `recipe_recipe` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=267 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recipe_recipe_ingredient`
--

LOCK TABLES `recipe_recipe_ingredient` WRITE;
/*!40000 ALTER TABLE `recipe_recipe_ingredient` DISABLE KEYS */;
INSERT INTO `recipe_recipe_ingredient` VALUES (19,'2 porcje ',2,2),(20,'z przepisu ',3,2),(21,'2 szklanka',4,2),(22,'1 mała ',5,2),(23,'1 łodyga ',6,2),(24,'1/2 sztuk',7,2),(25,'2 ząbki ',8,2),(26,'2 łyżeczka',9,2),(27,'1/2 szklanka',10,2),(28,' ',11,2),(29,' ',12,2),(30,'kilka łyżka',13,2),(31,' ',14,2),(32,' ',15,2),(33,'300 gramy',16,3),(34,'1/4 szklanka',17,3),(35,'3-4 łyżka',18,3),(36,'1 łyżeczka',19,3),(37,'1 łyżeczka',20,3),(38,' ',11,3),(39,' ',12,3),(40,'1 łyżeczka',21,3),(41,'1,5 łyżeczka',22,3),(42,'1 szklanka',23,4),(43,'4 szklanki ciętych liści ',24,4),(44,'4 łyżka',25,4),(45,'600 gramy',26,4),(46,'2 sztuk',27,4),(47,'2 sztuk',28,4),(48,'3 ząbki ',8,4),(49,'1 łyżeczka',29,4),(50,'1 łyżeczka',30,4),(51,'1 łyżeczka',31,4),(52,'1 sztuk',32,4),(53,'160 gramy',33,4),(54,'4 łyżka',9,4),(55,'3/4 kilogramy',34,5),(56,'3/4 kilogramy',7,5),(57,'2 szklanka',35,5),(58,' ',36,5),(59,' ',11,5),(60,' ',12,5),(61,'1 kilogramy',37,6),(62,'1 łyżka',38,6),(63,'1 szklanka',39,6),(64,'1 łyżka',40,6),(65,'1 łyżka',41,6),(66,' ',11,6),(67,'2 sztuk',42,7),(68,'1/4 szklanka',43,7),(69,'1 łyżeczka',44,7),(70,'1/2 łyżeczka',45,7),(71,' ',46,7),(72,' ',11,7),(73,' ',12,7),(74,'1 łyżeczka',38,7),(75,'200 gramy',47,8),(76,'100 gramy',48,8),(77,'450 gramy',49,8),(78,'2 sztuk',7,8),(79,'4 ząbki ',8,8),(80,'1/2 sztuk',32,8),(81,'2 łodygi ',6,8),(82,'1 łyżka',50,8),(83,'1 łyżeczka',29,8),(84,'1 łyżeczka',51,8),(85,'z połowy ',46,8),(86,' ',52,8),(87,'3 łyżka',9,8),(88,' ',53,8),(89,' ',12,8),(90,' ',54,8),(91,'100 gramy',55,9),(92,'2 łyżka',38,9),(93,'2 łyżeczka',51,9),(94,'450 gramy',56,9),(95,'1/2 szklanka',13,9),(96,'1/3 szklanka',39,9),(97,'500 gramy',57,9),(98,'lub koperek ',41,9),(99,' ',58,9),(100,' ',44,9),(101,' ',9,9),(102,'500 gramy',59,10),(103,'1 mała ',60,10),(104,'1 sztuk',61,10),(105,'1 sztuk',62,10),(106,'1 sztuk',7,10),(107,'1 ząbek ',8,10),(108,'2 łyżka',9,10),(109,'1 łyżka',38,10),(110,'1/2 łyżeczka',63,10),(111,'szczypta ',52,10),(112,'1 szklanka',35,10),(113,'1 łyżeczka',64,10),(114,'1 łyżka',41,10),(115,'1/2 łyżeczka',44,10),(116,'1/2 łyżeczka',65,10),(117,'4-5 sztuk',66,10),(118,'250 gramy',44,11),(119,'150 mililitry',67,11),(120,'2 łyżka',9,11),(121,'3-4 gramy',68,11),(122,'1/2 łyżeczka',11,11),(123,'1/2 łyżeczka',45,11),(124,'2 łyżka',69,11),(125,'100 gramy',70,12),(126,'2 sztuk',60,12),(127,'1 sztuk',5,12),(128,'2 ząbki ',8,12),(129,'100 gramy',71,12),(130,'1 sztuk',72,12),(131,'pęczek ',73,12),(132,'50 mililitry',74,12),(133,' ',31,12),(134,'1 mała ',32,12),(135,' ',11,12),(136,'2 szklanka',70,13),(137,'2 sztuk',7,13),(138,'2 sztuk',5,13),(139,'2 sztuk',75,13),(140,'2 łyżeczka',63,13),(141,'1 duża szczypta ',51,13),(142,'1/2 szklanka',76,13),(143,' ',9,13),(144,'700 mililitry',4,13),(145,'2 ząbki ',8,13),(146,'garść ',14,13),(147,' ',15,13),(148,' ',41,13),(149,'150 gramy',47,14),(150,'2 puszki ',49,14),(151,'1500 mililitry',13,14),(152,'1,5 sztuk',7,14),(153,'3 ząbki ',8,14),(154,'2 łyżka',9,14),(155,' ',58,14),(156,'3 łyżeczka',29,14),(157,'3 łyżeczka',51,14),(158,'1,5 łyżeczka',77,14),(159,'3/4 szklanka',78,14),(160,'4 łyżka',41,14),(161,'1 puszka ',79,15),(162,'1 puszka ',80,15),(163,'1 puszka ',81,15),(164,'1 puszka ',49,15),(165,'1 opakowanie ',30,15),(166,'2 sztuk',7,15),(167,'4 ząbki ',8,15),(168,'1 sztuk',61,15),(169,'2 sztuk',82,15),(170,'2 łyżeczka',64,15),(171,'1 opakowanie ',83,15),(172,' ',84,15),(173,' ',69,15),(174,'4 kulki ',85,15),(175,' ',58,15),(176,'2 łyżka',9,16),(177,'1/2 sztuk',7,16),(178,'1 sztuk',5,16),(179,'2 ząbki ',8,16),(180,'1 szklanka',13,16),(181,'1 puszka ',81,16),(182,'1 puszka ',49,16),(183,'1 łyżka',64,16),(184,'1/2 łyżeczka',63,16),(185,'1/2 łyżeczka',86,16),(186,'1/2 sztuk',60,16),(187,'garść ',87,16),(188,' ',14,16),(189,' ',15,16),(190,'5 sztuk',72,17),(191,'2 łyżka',1,17),(192,'2 łyżka',39,17),(193,'10 sztuk',88,17),(194,'2 pęczki ',89,17),(195,'1 łyżeczka',90,17),(196,'1 pęczek ',91,17),(197,' ',58,17),(198,'1 sztuk',72,18),(199,'1 łyżeczka',92,18),(200,'2 łyżka',93,18),(201,'350 mililitry',21,18),(202,' ',58,18),(203,'700 mililitry',4,19),(204,'(sucha) 100 gramy',70,19),(205,'1,5 szklanka',94,19),(206,'1 laska ',95,19),(207,'90 gramy',96,19),(208,'2 łyżeczka',97,19),(209,'10 sztuk',98,19),(210,'2 łyżka',99,19),(211,'3 łyżeczka',100,19),(212,'100 gramy',101,19),(213,'20 mililitry',94,19),(214,'1 łyżeczka',97,19),(215,'200g (zimne, min 82%) ',38,20),(216,'2,5 szklanka',44,20),(217,'1,5 łyżeczka',102,20),(218,'2 szczypty ',11,20),(219,'4 łyżka',45,20),(220,'4 sztuk',72,20),(221,'1 szklanka',103,20),(222,'2 łyżka',65,20),(223,'2 łyżka',104,20),(224,'500 mililitry',105,20),(225,'500 gramy',44,21),(226,'200 mililitry',43,21),(227,'2 sztuk',72,21),(228,'30 gramy',106,21),(229,'1 paczka ',107,21),(230,'1 łyżeczka',45,21),(231,'80 gramy',38,21),(232,' ',11,21),(233,' ',108,21),(234,'3 duże ',61,22),(235,'3 ząbki ',8,22),(236,'1 duża ',7,22),(237,'4 łyżki ',25,22),(238,'4 łyżki ',4,22),(239,'1/2 paczki ',110,22),(240,'4 łyżki ',17,22),(241,'1 paczka ',111,22),(242,' ',73,22),(243,'1 łyżka ',63,22),(244,'1/2 łyżeczka',22,22),(245,'1/2 łyżeczka',11,22),(246,'50 mililitry',67,22),(247,'1 łyżka',46,22),(248,'2 paczki ',112,23),(249,'200 gramy',113,23),(250,'200 gramy',114,23),(251,'2 małe ',60,23),(252,'1 puszka ',80,23),(253,'1 puszka (opcjonalnie) ',115,23),(254,'1 sztuk',7,23),(255,'1 ząbek ',8,23),(256,'2 łyżki ',64,23),(257,' ',58,23),(258,'5-6 łyżek ',116,23),(259,'1 łyżka ',63,23),(260,'0.5 łyżki ',86,23),(261,'1 łyżka',117,23),(262,'1 łyżeczka',118,23),(263,'pół suszonej ',32,23),(264,'1/3 łyżeczka',119,23),(265,'2 łyżka',17,23),(266,'pół szklanki ',120,23);
/*!40000 ALTER TABLE `recipe_recipe_ingredient` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recipe_recipe_tags`
--

DROP TABLE IF EXISTS `recipe_recipe_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recipe_recipe_tags` (
  `id` int NOT NULL AUTO_INCREMENT,
  `recipe_id` int NOT NULL,
  `tag_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `recipe_recipe_tag_recipe_id_tag_id_e4d78348_uniq` (`recipe_id`,`tag_id`),
  KEY `recipe_recipe_tags_tag_id_ee78e406_fk_recipe_tag_id` (`tag_id`),
  CONSTRAINT `recipe_recipe_tags_recipe_id_01e493ee_fk_recipe_recipe_id` FOREIGN KEY (`recipe_id`) REFERENCES `recipe_recipe` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `recipe_recipe_tags_tag_id_ee78e406_fk_recipe_tag_id` FOREIGN KEY (`tag_id`) REFERENCES `recipe_tag` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=48 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recipe_recipe_tags`
--

LOCK TABLES `recipe_recipe_tags` WRITE;
/*!40000 ALTER TABLE `recipe_recipe_tags` DISABLE KEYS */;
INSERT INTO `recipe_recipe_tags` VALUES (1,2,3),(2,2,8),(3,3,3),(4,3,11),(5,4,4),(6,4,8),(7,5,6),(8,5,8),(9,6,4),(10,6,8),(11,7,4),(12,7,8),(13,8,4),(14,8,8),(15,9,4),(16,9,8),(17,10,6),(18,10,8),(19,11,4),(20,11,8),(21,12,3),(22,12,8),(23,13,3),(24,13,8),(25,14,4),(26,14,7),(27,15,3),(28,15,7),(29,16,3),(30,16,7),(31,17,4),(32,17,11),(33,18,4),(34,18,11),(35,19,4),(36,19,9),(37,20,4),(38,20,9),(39,21,4),(40,21,9),(41,22,3),(42,22,8),(43,23,3),(44,23,8),(45,24,3),(46,24,10),(47,34,4);
/*!40000 ALTER TABLE `recipe_recipe_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recipe_tag`
--

DROP TABLE IF EXISTS `recipe_tag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recipe_tag` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(25) NOT NULL,
  `slug` varchar(50) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `recipe_tag_user_id_name_1c42cfb5_uniq` (`user_id`,`name`),
  KEY `recipe_tag_slug_394102a0` (`slug`),
  CONSTRAINT `recipe_tag_user_id_98ae3fd7_fk_users_myuser_id` FOREIGN KEY (`user_id`) REFERENCES `users_myuser` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recipe_tag`
--

LOCK TABLES `recipe_tag` WRITE;
/*!40000 ALTER TABLE `recipe_tag` DISABLE KEYS */;
INSERT INTO `recipe_tag` VALUES (1,'Przyprawa','przyprawa',1),(3,'Wegańskie','weganskie',1),(4,'Wegetariańskie','wegetarianskie',1),(6,'Mięsne','miesne',1),(7,'Zupa','zupa',1),(8,'Obiad','obiad',1),(9,'Deser','deser',1),(10,'Sałatka','salatka',1),(11,'Inne','inne',1);
/*!40000 ALTER TABLE `recipe_tag` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_myuser`
--

DROP TABLE IF EXISTS `users_myuser`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_myuser` (
  `id` int NOT NULL AUTO_INCREMENT,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `email` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `sex` varchar(5) NOT NULL,
  `age` int NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_myuser`
--

LOCK TABLES `users_myuser` WRITE;
/*!40000 ALTER TABLE `users_myuser` DISABLE KEYS */;
INSERT INTO `users_myuser` VALUES (1,'2021-05-01 10:03:40.623355',1,'pstaszczuk1@gmail.com','Patryk','pbkdf2_sha256$216000$wCzShcTNtNNg$tTVBew75lEEfjOP31cWGuTIDCxGrD36DHECnl4IyvNA=','Male',25,1,1);
/*!40000 ALTER TABLE `users_myuser` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_myuser_groups`
--

DROP TABLE IF EXISTS `users_myuser_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_myuser_groups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `myuser_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `users_myuser_groups_myuser_id_group_id_701de95c_uniq` (`myuser_id`,`group_id`),
  KEY `users_myuser_groups_group_id_320a3e7b_fk_auth_group_id` (`group_id`),
  CONSTRAINT `users_myuser_groups_group_id_320a3e7b_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `users_myuser_groups_myuser_id_6c79e2c5_fk_users_myuser_id` FOREIGN KEY (`myuser_id`) REFERENCES `users_myuser` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_myuser_groups`
--

LOCK TABLES `users_myuser_groups` WRITE;
/*!40000 ALTER TABLE `users_myuser_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `users_myuser_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_myuser_user_permissions`
--

DROP TABLE IF EXISTS `users_myuser_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users_myuser_user_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `myuser_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `users_myuser_user_permis_myuser_id_permission_id_bfff4a24_uniq` (`myuser_id`,`permission_id`),
  KEY `users_myuser_user_pe_permission_id_6f8831ec_fk_auth_perm` (`permission_id`),
  CONSTRAINT `users_myuser_user_pe_myuser_id_7135c2f9_fk_users_myu` FOREIGN KEY (`myuser_id`) REFERENCES `users_myuser` (`id`),
  CONSTRAINT `users_myuser_user_pe_permission_id_6f8831ec_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_myuser_user_permissions`
--

LOCK TABLES `users_myuser_user_permissions` WRITE;
/*!40000 ALTER TABLE `users_myuser_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `users_myuser_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2021-05-03 14:12:34
