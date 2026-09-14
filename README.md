# Transcrever vídeo para texto

Este projeto usa o `faster-whisper` para transcrever o áudio de um vídeo e gerar:

- um arquivo `.txt` com a transcrição e timestamps;
- um arquivo `.srt` para usar como legenda.

O modelo padrão é o `medium`, que tende a produzir um resultado melhor que o
`small`, especialmente em áudios com ruído ou falas mais difíceis. Em troca, a
transcrição pode demorar mais e consumir mais memória.

## Requisitos

- macOS;
- Python 3.9 ou mais recente;
- Homebrew, recomendado para instalar o `ffmpeg`;
- espaço em disco para baixar o modelo do Whisper na primeira execução.

## Instalação do zero

Abra o Terminal e entre na pasta do projeto:

```bash
cd /caminho/para/transcrever
```

O `ffmpeg` é usado para extrair o áudio do vídeo. Primeiro, verifique se ele já
está instalado:

```bash
ffmpeg -version
```

Se aparecer `command not found`, instale o Homebrew. Este é o gerenciador de
pacotes mais comum no macOS; o instalador oficial funciona tanto em Macs com
Apple Silicon quanto em Macs Intel:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Ao final da instalação, siga a instrução exibida pelo instalador para adicionar
o Homebrew ao `PATH`. Feche e abra o Terminal novamente. Depois, instale o
`ffmpeg`:

```bash
brew install ffmpeg
```

Se o Homebrew já estiver instalado, mas aparecer `zsh: command not found:
brew`, configure o caminho manualmente e abra um novo Terminal:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Em Macs Intel, use `/usr/local/bin/brew` no lugar de
`/opt/homebrew/bin/brew`.

Confirme que a instalação funcionou:

```bash
ffmpeg -version
```

Crie um ambiente virtual Python e ative-o:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Mesmo que o comando global `python` não exista no macOS, o ambiente virtual
possui seu próprio executável. Use-o nos comandos abaixo:

Instale as dependências:

```bash
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
```

## Como executar

Coloque o vídeo na pasta do projeto e execute:

```bash
./.venv/bin/python transcribe_video.py nome_do_video.mp4
```

Por exemplo:

```bash
./.venv/bin/python transcribe_video.py reuniao.mp4
```

Ao terminar, serão criados automaticamente:

```text
reuniao.txt
reuniao.srt
```

O arquivo `.txt` inclui timestamps por padrão. Para gerar somente o texto:

```bash
./.venv/bin/python transcribe_video.py reuniao.mp4 --no-timestamps
```

Para definir outro nome para a transcrição, informe o segundo argumento. O
arquivo `.srt` usará o mesmo nome base:

```bash
./.venv/bin/python transcribe_video.py reuniao.mp4 resultado.txt
```

## Qualidade e velocidade

O modelo pode ser escolhido com `--model`:

| Modelo | Resultado esperado | Uso de recursos |
| --- | --- | --- |
| `small` | bom | menor |
| `medium` | melhor equilíbrio e padrão do projeto | médio/alto |
| `large-v3` | melhor qualidade | alto |

Exemplo para priorizar ainda mais a qualidade:

```bash
./.venv/bin/python transcribe_video.py reuniao.mp4 --model large-v3
```

O idioma padrão é português (`pt`). Para outro idioma, use `--language`, por
exemplo `--language en`. O programa tenta usar GPU quando configurado e muda
automaticamente para CPU se ela não estiver disponível. No macOS, a execução
em CPU é o caminho mais compatível, mas pode ser mais lenta.

## Primeira execução

Na primeira execução, o modelo escolhido será baixado automaticamente. Esse
download pode ser grande e a transcrição do primeiro vídeo pode demorar mais;
as execuções seguintes reaproveitam o modelo instalado.

Se aparecer a mensagem `ffmpeg não encontrado`, confirme que o comando abaixo
funciona no Terminal:

```bash
ffmpeg -version
```
