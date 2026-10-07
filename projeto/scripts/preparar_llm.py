"""Obtém um snapshot fixo do gerador local. Não envia dados do projeto ao Hugging Face."""
from pathlib import Path
import json
from huggingface_hub import HfApi,snapshot_download
ROOT=Path(__file__).resolve().parents[1]

def main():
    repo='Qwen/Qwen2.5-0.5B-Instruct'; cache=ROOT/'.hf_cache'
    manifest=ROOT/'models/llm_manifest.json'
    revision=json.loads(manifest.read_text(encoding='utf-8'))['revision'] if manifest.exists() else HfApi().model_info(repo).sha
    snapshot_download(repo_id=repo,revision=revision,local_dir=ROOT/'models/llm',cache_dir=cache,
                      allow_patterns=['*.json','*.safetensors','merges.txt','vocab.json','LICENSE','README.md'])
    (ROOT/'models/llm_manifest.json').write_text(json.dumps({'repo_id':repo,'revision':revision,'license':'Apache-2.0',
        'local_directory':'models/llm','training':'Modelo pré-treinado pelos autores; não afinado neste projeto.'},indent=2,ensure_ascii=False),encoding='utf-8')
    print('Modelo local disponível:',repo,revision)
if __name__=='__main__':main()
