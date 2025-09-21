#!/usr/bin/env bash
# Script: dev_snapshot.sh
# Objetivo: crear un snapshot de trabajo (sin usar git comandos si git no está disponible)
# 1. Lee hash HEAD si existe
# 2. Genera nombre de archivo tar comprimido excluyendo artefactos
# 3. Crea manifest con metadatos
# 4. Empaqueta
# Uso: ./scripts/dev_snapshot.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="$ROOT_DIR/_snapshots"
mkdir -p "$OUT_DIR"

HEAD_REF_FILE="$ROOT_DIR/.git/HEAD"
HASH=""
if [[ -f "$HEAD_REF_FILE" ]]; then
  if grep -q '^ref:' "$HEAD_REF_FILE"; then
    REF_PATH=$(cut -d' ' -f2 < "$HEAD_REF_FILE")
    if [[ -f "$ROOT_DIR/.git/$REF_PATH" ]]; then
      HASH=$(cat "$ROOT_DIR/.git/$REF_PATH" | head -n1)
    fi
  else
    HASH=$(head -n1 "$HEAD_REF_FILE")
  fi
fi

SNAP_NAME="snapshot_${TIMESTAMP}_${HASH:0:8}"
TAR_FILE="$OUT_DIR/${SNAP_NAME}.tar.gz"
MANIFEST="$OUT_DIR/${SNAP_NAME}.manifest.txt"

# Crear manifest
{
  echo "Snapshot: $SNAP_NAME"
  echo "Fecha: $(date -Iseconds)"
  echo "HEAD Hash: ${HASH:-desconocido}" 
  echo "Exclusiones: .venv, __pycache__, *.log, .git (parcial)" 
  echo "Usuario: $(whoami)"
  echo "Hostname: $(hostname)"
} > "$MANIFEST"

# Empaquetar
# Incluimos .git para no perder refs pero lo comprimimos tal cual (sin excluir) excepto objetos grandes si existieran
# Si se quisiera excluir completamente .git, añadir: --exclude='.git'

tar -czf "$TAR_FILE" \
  --exclude='*.log' \
  --exclude='*.tmp' \
  --exclude='__pycache__' \
  --exclude='.venv' \
  -C "$ROOT_DIR" .

# Hash SHA256
SHA256=$(sha256sum "$TAR_FILE" | awk '{print $1}')
{
  echo "SHA256: $SHA256"
} >> "$MANIFEST"

echo "Snapshot creado: $TAR_FILE"
echo "Manifest: $MANIFEST"
