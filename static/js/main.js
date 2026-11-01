// 可以在这里添加一些简单的交互，例如确认弹窗
document.addEventListener('DOMContentLoaded', () => {
    // 给所有“发起互换”按钮加一个确认提示
    const swapBtns = document.querySelectorAll('.btn-primary');
    // 注：由于主页的匹配可能为空，这里只做简单的静态绑定
    console.log("技能互换平台已加载完成！");
});