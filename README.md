## youtube影片下載器。

## For Developer

### 建立虛擬環境

1. 安裝 `virtualenv`：
    ```sh
    pip install virtualenv
    ```

2. 建立虛擬環境：
    ```sh
    virtualenv myenv
    ```

3. 啟動虛擬環境：
    - Windows:
        ```sh
        .\myenv\Scripts\activate
        ```
    - macOS/Linux:
        ```sh
        source myenv/bin/activate
        ```

### 安裝套件

在虛擬環境啟動後，執行：
```sh
pip install -r requirements.txt
```

### 編譯exe檔

```sh
pyinstaller main.spec
```