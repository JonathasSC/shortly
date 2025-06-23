class TextUtils{
    copyText(targetId){
        const text = document.getElementById(targetId).value;
        navigator.clipboard.writeText(text);
    }
}