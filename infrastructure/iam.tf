resource "google_service_account" "liver_disease" {
  account_id   = "liver-disease-mlops"
  display_name = "liver Disease MLOps Pipeline Service Account"
}

resource "google_project_iam_member" "lv_storage_admin" {
  project = "neat-chain-464913-k3" 
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.liver_disease.email}"
}

resource "google_project_iam_member" "lv_storage_viewer" {
  project = "neat-chain-464913-k3"
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.liver_disease.email}"
}

resource "google_project_iam_member" "lv_owner" {
  project = "neat-chain-464913-k3"
  role    = "roles/owner"
  member  = "serviceAccount:${google_service_account.liver_disease.email}"
}

resource "google_service_account_key" "liver_disease_key" {
  service_account_id = google_service_account.liver_disease.name
}

resource "local_file" "lv_key_file" {
  content  = base64decode(google_service_account_key.liver_disease_key.private_key)
  filename = "${path.module}/liver-disease-gcp-key.json"
}

resource "google_storage_bucket_iam_member" "bucket_object_admin" {
  bucket = google_storage_bucket.mlops_artifacts_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.liver_disease.email}"
}

resource "google_storage_bucket_iam_member" "bucket_object_viewer_bucket_level" {
  bucket = google_storage_bucket.mlops_artifacts_bucket.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.liver_disease.email}"
}