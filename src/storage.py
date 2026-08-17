"""Módulo de armazenamento com suporte a Cloudflare R2 e fallback local.

Quando as variáveis de ambiente R2_ENDPOINT_URL, R2_ACCESS_KEY_ID e
R2_SECRET_ACCESS_KEY estão definidas, todos os arquivos são salvos/lidos
do bucket R2 (persistente no Railway).

Sem essas variáveis (desenvolvimento local), usa o disco local normalmente.
"""
import os

_r2_client = None
_r2_bucket = None
_r2_checked = False


def _get_client():
    global _r2_client, _r2_bucket, _r2_checked
    if _r2_checked:
        return _r2_client, _r2_bucket

    _r2_checked = True
    endpoint  = os.environ.get("R2_ENDPOINT_URL", "").strip()
    access_key = os.environ.get("R2_ACCESS_KEY_ID", "").strip()
    secret_key = os.environ.get("R2_SECRET_ACCESS_KEY", "").strip()
    bucket     = os.environ.get("R2_BUCKET_NAME", "cop-dashboard").strip()

    if not all([endpoint, access_key, secret_key]):
        return None, None

    try:
        import boto3
        _r2_client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="auto",
        )
        _r2_bucket = bucket
    except Exception:
        _r2_client = None
        _r2_bucket = None

    return _r2_client, _r2_bucket


def r2_available() -> bool:
    """Retorna True se o R2 está configurado e acessível."""
    client, _ = _get_client()
    return client is not None


def upload(key: str, data: bytes) -> bool:
    """Envia bytes para o R2. Retorna True em caso de sucesso."""
    client, bucket = _get_client()
    if client is None:
        return False
    try:
        client.put_object(Bucket=bucket, Key=key, Body=data)
        return True
    except Exception:
        return False


def download(key: str) -> bytes | None:
    """Baixa bytes do R2. Retorna None se não encontrado ou erro."""
    client, bucket = _get_client()
    if client is None:
        return None
    try:
        response = client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()
    except Exception as e:
        # NoSuchKey → arquivo ainda não existe, retorna None silenciosamente
        err = getattr(e, "response", {}).get("Error", {}).get("Code", "")
        if err in ("NoSuchKey", "404"):
            return None
        return None


def exists(key: str) -> bool:
    """Verifica se uma chave existe no R2."""
    client, bucket = _get_client()
    if client is None:
        return False
    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except Exception:
        return False
