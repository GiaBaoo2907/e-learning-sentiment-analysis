const $ = (s, r = document) => r.querySelector(s);
const app = $('#app');
const modalRoot = $('#modal-root');
const tokenKey = 'edupulse_access_token';
const sentimentNames = ['Tiêu cực', 'Trung tính', 'Tích cực'];
const sentimentClasses = ['negative', 'neutral', 'positive'];
let token = localStorage.getItem(tokenKey) || '';
let me = null;
let categories = [];
let currentCourse = null;
let currentView = 'catalog';
let editFeedback = null;
let devResetToken = '';

const escapeHtml = (value = '') => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(path, options = {}) {
  const headers = {'Content-Type': 'application/json', ...(options.headers || {})};
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(path, {...options, headers});
  const data = response.status === 204 ? null : await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && token) { signOut(); }
    throw new Error(data?.detail || 'Đã xảy ra lỗi. Vui lòng thử lại.');
  }
  return data;
}
function toast(message, error = false) {
  const el = document.createElement('div'); el.className = `toast ${error ? 'toast-error' : ''}`; el.textContent = message;
  document.body.append(el); setTimeout(() => el.remove(), 3200);
}
function videoEmbed(raw) {
  try {
    const url = new URL(raw);
    if (!['https:', 'http:'].includes(url.protocol)) return '';
    if (url.hostname.includes('youtu.be')) return `https://www.youtube-nocookie.com/embed/${encodeURIComponent(url.pathname.slice(1))}`;
    if (url.hostname.includes('youtube.com')) {
      const id = url.searchParams.get('v') || url.pathname.match(/\/embed\/([^/]+)/)?.[1];
      return id ? `https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}` : '';
    }
    return url.href;
  } catch { return ''; }
}

function renderAuth(mode = 'login', message = '') {
  const register = mode === 'register';
  app.innerHTML = `<main class="auth-page"><div class="auth-brand"><span class="logo-mark">e</span><span>Edu<span>Pulse</span></span></div>
    <section class="auth-card"><div class="eyebrow">NỀN TẢNG HỌC TẬP TRỰC TUYẾN</div><h1>${register ? 'Tạo tài khoản' : mode === 'reset' ? 'Đặt lại mật khẩu' : 'Chào mừng trở lại'}</h1>
    <p class="muted">${register ? 'Bắt đầu hành trình học tập của bạn.' : mode === 'reset' ? 'Nhập mã và mật khẩu mới của bạn.' : 'Đăng nhập để tiếp tục khóa học.'}</p>
    ${message ? `<div class="notice">${escapeHtml(message)}</div>` : ''}
    <form id="auth-form" class="stack-form">
      ${register ? '<label>Họ và tên<input name="full_name" minlength="2" maxlength="120" required placeholder="Nguyễn Minh Anh"></label>' : ''}
      ${mode !== 'reset' ? '<label>Email<input name="email" type="email" required placeholder="ban@example.com" autocomplete="email"></label>' : `<label>Mã đặt lại mật khẩu<input name="token" required minlength="20" value="${escapeHtml(devResetToken)}"></label>`}
      ${mode !== 'forgot' ? `<label>${mode === 'reset' ? 'Mật khẩu mới' : 'Mật khẩu'}<input name="password" type="password" minlength="8" maxlength="128" required autocomplete="${register || mode === 'reset' ? 'new-password' : 'current-password'}"></label>` : ''}
      <button class="btn btn-primary btn-wide" type="submit">${register ? 'Đăng ký' : mode === 'reset' ? 'Cập nhật mật khẩu' : mode === 'forgot' ? 'Gửi hướng dẫn' : 'Đăng nhập'} <span>↗</span></button>
    </form>
    <div id="auth-result" class="auth-result" aria-live="polite"></div>
    <div class="auth-links">${mode === 'login' ? '<button data-auth="forgot">Quên mật khẩu?</button><span>Chưa có tài khoản? <button data-auth="register">Đăng ký</button></span>' : '<button data-auth="login">← Quay lại đăng nhập</button>'}</div>
    </section><p class="auth-foot">HỌC TẬP · KẾT NỐI · PHÁT TRIỂN</p></main>`;
  $('[data-auth="register"]')?.addEventListener('click', () => renderAuth('register'));
  $('[data-auth="forgot"]')?.addEventListener('click', () => renderAuth('forgot'));
  $('[data-auth="login"]')?.addEventListener('click', () => renderAuth('login'));
  $('#auth-form').addEventListener('submit', async e => {
    e.preventDefault(); const form = Object.fromEntries(new FormData(e.currentTarget).entries());
    const out = $('#auth-result'); out.textContent = 'Đang xử lý…';
    try {
      let data;
      if (mode === 'register') data = await api('/api/auth/register', {method:'POST', body:JSON.stringify(form)});
      else if (mode === 'login') data = await api('/api/auth/login', {method:'POST', body:JSON.stringify(form)});
      else if (mode === 'forgot') {
        data = await api('/api/auth/forgot-password', {method:'POST', body:JSON.stringify(form)});
        out.textContent = data.development_token ? `${data.message} Mã demo: ${data.development_token}` : data.message;
        if (data.development_token) devResetToken=data.development_token;
        const b = document.createElement('button'); b.className='text-button'; b.textContent='Nhập mã đặt lại mật khẩu'; b.onclick=()=>renderAuth('reset'); out.append(document.createElement('br'), b);
        return;
      } else {
        data = await api('/api/auth/reset-password', {method:'POST', body:JSON.stringify({token:form.token,new_password:form.password})});
        devResetToken=''; renderAuth('login', data.message); return;
      }
      token = data.access_token; me = data.user; localStorage.setItem(tokenKey, token);
      if (me.role === 'admin') location.href = '/admin'; else renderApp();
    } catch (err) { out.textContent = err.message; out.className='auth-result error-text'; }
  });
}

function shell(content) {
  app.innerHTML = `<div class="app-shell"><aside class="sidebar"><a class="side-brand" href="/"><span class="logo-mark">e</span><span>Edu<span>Pulse</span></span></a>
    <div class="side-label">KHÔNG GIAN HỌC TẬP</div><nav class="side-nav">
      <button data-view="catalog" class="${currentView==='catalog'?'active':''}"><span>⌕</span> Khám phá khóa học</button>
      <button data-view="learning" class="${currentView==='learning'?'active':''}"><span>▤</span> Khóa học của tôi</button>
      <button data-view="reviews" class="${currentView==='reviews'?'active':''}"><span>✳</span> Đánh giá của tôi</button>
    </nav><div class="side-bottom"><div class="mini-profile"><span class="avatar">${escapeHtml((me?.full_name||'SV').slice(0,1).toUpperCase())}</span><div><b>${escapeHtml(me?.full_name||'Sinh viên')}</b><small>Sinh viên</small></div></div><button id="signout" class="signout">↪ Đăng xuất</button></div></aside>
    <main class="main-area"><header class="main-header"><div><span class="header-kicker">E-LEARNING · STUDENT SPACE</span><h2>${currentView==='catalog'?'Khám phá tri thức':currentView==='learning'?'Tiếp tục học tập':currentView==='reviews'?'Đánh giá của tôi':escapeHtml(currentCourse?.title||'Chi tiết khóa học')}</h2></div><button class="profile-chip" data-view="profile"><span class="avatar avatar-small">${escapeHtml((me?.full_name||'SV').slice(0,1).toUpperCase())}</span>${escapeHtml(me?.full_name||'Sinh viên')} <span>⌄</span></button></header><div class="page-content">${content}</div></main></div>`;
  $$('[data-view]').forEach(btn => btn.addEventListener('click', () => { currentView=btn.dataset.view; currentCourse=null; renderApp(); }));
  $('#signout')?.addEventListener('click', signOut);
}
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

async function renderCatalog() {
  categories = await api('/api/categories');
  const [courses, myCourses] = await Promise.all([api('/api/courses'), api('/api/student/courses')]);
  const mine = new Set(myCourses.map(c => c.id));
  shell(`<section class="hero-strip"><div><span class="eyebrow">HỌC THEO CÁCH CỦA BẠN</span><h1>Mỗi ngày một bước<br><span>gần hơn mục tiêu.</span></h1><p>Chọn khóa học phù hợp và bắt đầu tiến bộ ngay hôm nay.</p></div><div class="hero-graphic"><div class="orbit orbit-one"></div><div class="orbit orbit-two"></div><div class="hero-book">✦</div><span class="float-tag tag-a">LEARN</span><span class="float-tag tag-b">GROW</span></div></section>
    <div class="section-toolbar"><div><span class="eyebrow">THƯ VIỆN KHÓA HỌC</span><h3>Tìm điều bạn muốn học</h3></div><div class="filters"><label class="searchbox">⌕ <input id="course-search" placeholder="Tìm khóa học..."></label><select id="category-filter"><option value="">Tất cả danh mục</option>${categories.map(c=>`<option value="${c.id}">${escapeHtml(c.name)}</option>`).join('')}</select></div></div>
    <div id="course-grid" class="course-grid">${courseCards(courses, mine)}</div>`);
  $('#course-search').addEventListener('input', filterCourses);
  $('#category-filter').addEventListener('change', filterCourses);
  function filterCourses() {
    const q=$('#course-search').value.toLocaleLowerCase('vi'), cat=$('#category-filter').value;
    const filtered=courses.filter(c=>(!q||`${c.title} ${c.instructor} ${c.description}`.toLocaleLowerCase('vi').includes(q))&&(!cat||c.category_id===Number(cat)));
    $('#course-grid').innerHTML=courseCards(filtered,mine); bindCourseCards();
  }
  bindCourseCards();
}
function courseCards(courses, mine) {
  if(!courses.length) return '<div class="empty-state">Chưa có khóa học được xuất bản. Quản trị viên có thể thêm khóa học trong trang quản trị.</div>';
  const art=['art-violet','art-peach','art-mint','art-blue'];
  return courses.map((c,i)=>`<article class="course-card"><div class="course-cover ${art[i%4]}">${c.thumbnail_url?`<img src="${escapeHtml(c.thumbnail_url)}" alt="">`:`<div class="cover-symbol">${['◈','✳','⌘','◌'][i%4]}</div>`}<span class="cover-category">${escapeHtml(c.category.name)}</span></div><div class="course-body"><h4>${escapeHtml(c.title)}</h4><p class="course-instructor">Hướng dẫn bởi <b>${escapeHtml(c.instructor)}</b></p><div class="course-meta"><span>▤ ${c.lesson_count} bài giảng</span>${mine.has(c.id)?`<span class="progress-mini">${c.progress_percent}% hoàn thành</span>`:'<span>✦ Khóa học</span>'}</div><button class="btn ${mine.has(c.id)?'btn-outline':'btn-primary'} btn-small" data-course="${c.id}">${mine.has(c.id)?'Tiếp tục học':'Xem khóa học'} <span>↗</span></button></div></article>`).join('');
}
function bindCourseCards(){ $$('[data-course]').forEach(b=>b.addEventListener('click',()=>openCourse(Number(b.dataset.course)))); }

async function openCourse(id) {
  const course=await api(`/api/courses/${id}`); currentCourse=course; currentView='detail';
  const enrolled=course.enrolled;
  const lessons=course.lessons.map(l=>`<div class="lesson-item"><div class="lesson-play">${l.completed?'✓':'▶'}</div><div class="lesson-copy"><b>${escapeHtml(l.title)}</b><small>${escapeHtml(l.description||'Bài giảng video')} · ${l.duration_seconds?Math.ceil(l.duration_seconds/60)+' phút':'Video'}</small></div>${enrolled?`<button class="btn btn-outline btn-xs" data-lesson="${l.id}">${l.completed?'Xem lại':'Học bài'} ↗</button>`:'<span class="lock-icon">▣</span>'}</div>`).join('')||'<p class="muted">Khóa học chưa có bài giảng.</p>';
  shell(`<button class="back-link" id="back-catalog">← Quay lại danh sách khóa học</button><section class="detail-hero"><div><span class="eyebrow">${escapeHtml(course.category.name)}</span><h1>${escapeHtml(course.title)}</h1><p>${escapeHtml(course.description)}</p><div class="detail-by">Giảng viên <b>${escapeHtml(course.instructor)}</b></div>${enrolled?`<div class="progress-line"><div><span>Tiến độ học</span><b>${course.progress_percent}%</b></div><div class="track"><div class="bar" style="width:${course.progress_percent}%"></div></div></div>`:`<button id="enroll" class="btn btn-primary">Ghi danh miễn phí <span>↗</span></button>`}</div><div class="detail-art"><div class="detail-art-icon">✦</div><div class="detail-art-label">${course.lesson_count} BÀI GIẢNG</div></div></section><section class="detail-columns"><div class="card-panel"><div class="panel-title"><div><span class="eyebrow">LỘ TRÌNH HỌC</span><h3>Nội dung khóa học</h3></div><span class="pill">${course.lesson_count} bài</span></div><div class="lesson-list">${lessons}</div></div><div class="card-panel review-panel"><span class="eyebrow">ĐÁNH GIÁ</span><h3>Chia sẻ trải nghiệm</h3><p class="muted">${enrolled?'Hoàn thành bài học để gửi đánh giá cho bài giảng hoặc toàn khóa.':'Ghi danh khóa học để bắt đầu học và gửi đánh giá.'}</p>${enrolled?`<div class="progress-note">Đã hoàn thành ${course.completed_lessons}/${course.lesson_count} bài giảng</div>`:''}</div></section>`);
  $('#back-catalog').onclick=()=>{currentCourse=null;currentView='catalog';renderApp()};
  $('#enroll')?.addEventListener('click',async()=>{try{await api(`/api/courses/${id}/enroll`,{method:'POST'});toast('Đã ghi danh khóa học.');openCourse(id)}catch(e){toast(e.message,true)}});
  $$('[data-lesson]').forEach(b=>b.addEventListener('click',()=>openLesson(id,Number(b.dataset.lesson))));
  if(enrolled){const fresh=await api(`/api/student/courses`);const ours=fresh.find(c=>c.id===id);if(ours){currentCourse=ours; renderCourseReview(ours);}}
}

function renderCourseReview(course){
  const panel=$('.review-panel'); if(!panel)return;
  const canCourse=course.lesson_count>0&&course.completed_lessons===course.lesson_count;
  panel.innerHTML=`<span class="eyebrow">ĐÁNH GIÁ</span><h3>Chia sẻ trải nghiệm</h3><p class="muted">Bạn có thể đánh giá từng bài đã hoàn thành hoặc toàn khóa khi hoàn thành lộ trình.</p><div class="progress-note">Đã hoàn thành ${course.completed_lessons}/${course.lesson_count} bài giảng</div>${canCourse?'<button class="btn btn-primary btn-small" id="review-course">Đánh giá khóa học ✦</button>':'<span class="pill">Hoàn thành toàn khóa để đánh giá</span>'}`;
  $('#review-course')?.addEventListener('click',()=>openFeedbackModal(course.id,null));
}

async function openLesson(courseId,lessonId){
  const course=await api(`/api/courses/${courseId}`); const lesson=course.lessons.find(l=>l.id===lessonId); if(!lesson)return;
  const src=videoEmbed(lesson.video_url);
  modalRoot.innerHTML=`<div class="modal-backdrop"><section class="modal lesson-modal"><button class="modal-close" aria-label="Đóng">×</button><span class="eyebrow">BÀI GIẢNG ${lesson.position}</span><h2>${escapeHtml(lesson.title)}</h2><p class="muted">${escapeHtml(lesson.description)}</p>${src?`<div class="video-frame"><iframe src="${escapeHtml(src)}" title="${escapeHtml(lesson.title)}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>`:'<div class="notice">Đường dẫn video chưa hợp lệ hoặc chưa được cấu hình.</div>'}<div class="modal-actions"><button class="btn btn-outline" id="lesson-review" ${lesson.completed?'':'disabled title="Hoàn thành bài giảng để đánh giá"'}>Đánh giá bài giảng</button><button class="btn btn-primary" id="mark-complete">${lesson.completed?'Đã hoàn thành ✓':'Đánh dấu hoàn thành'}</button></div></section></div>`;
  closeModal();
  $('#mark-complete').addEventListener('click',async()=>{try{await api(`/api/student/lessons/${lessonId}/progress?completed=true`,{method:'PUT'});toast('Đã cập nhật tiến độ.');modalRoot.innerHTML='';openCourse(courseId)}catch(e){toast(e.message,true)}});
  if(lesson.completed) $('#lesson-review').addEventListener('click',()=>openFeedbackModal(courseId,lessonId));
}

function openFeedbackModal(courseId,lessonId,feedback=null){
  editFeedback=feedback;
  modalRoot.innerHTML=`<div class="modal-backdrop"><section class="modal"><button class="modal-close" aria-label="Đóng">×</button><span class="eyebrow">PHẢN HỒI HỌC TẬP</span><h2>${feedback?'Chỉnh sửa đánh giá':'Bạn cảm nhận thế nào?'}</h2><form id="feedback-form" class="stack-form"><label>Điểm đánh giá<select name="rating" required>${[5,4,3,2,1].map(n=>`<option value="${n}" ${feedback?.rating===n?'selected':''}>${'★'.repeat(n)} (${n}/5)</option>`).join('')}</select></label><label>Nhận xét<textarea name="text" minlength="3" maxlength="5000" required placeholder="Chia sẻ cảm nhận thật của bạn…">${escapeHtml(feedback?.text||'')}</textarea></label><div class="muted small">Mô hình sẽ tự động phân tích cảm xúc cho nhận xét này.</div><button class="btn btn-primary btn-wide">${feedback?'Lưu thay đổi':'Gửi đánh giá'} ↗</button></form></section></div>`;
  closeModal();
  $('#feedback-form').addEventListener('submit',async e=>{e.preventDefault();const f=Object.fromEntries(new FormData(e.currentTarget));const data={...f,rating:Number(f.rating),course_id:courseId,lesson_id:lessonId};try{const result=await api(feedback?`/api/feedback/${feedback.id}`:'/api/feedback',{method:feedback?'PUT':'POST',body:JSON.stringify(data)});modalRoot.innerHTML='';toast(`Đã lưu đánh giá · ${result.sentiment_label}`);if(currentCourse)openCourse(currentCourse.id);else renderMyFeedback()}catch(err){toast(err.message,true)}});
}
function closeModal(){ $('.modal-close')?.addEventListener('click',()=>modalRoot.innerHTML=''); $('.modal-backdrop')?.addEventListener('click',e=>{if(e.target.classList.contains('modal-backdrop'))modalRoot.innerHTML=''}); }

async function renderLearning(){const courses=await api('/api/student/courses');shell(`<div class="section-toolbar"><div><span class="eyebrow">GHI DANH CỦA BẠN</span><h3>Học tiếp từ nơi bạn dừng lại</h3></div><button class="btn btn-outline" data-view="catalog">Khám phá thêm ↗</button></div>${courses.length?`<div class="learning-list">${courses.map(c=>`<article class="learning-card"><div class="learning-icon">✦</div><div class="learning-main"><span class="eyebrow">${escapeHtml(c.category.name)}</span><h3>${escapeHtml(c.title)}</h3><p>${escapeHtml(c.instructor)} · ${c.completed_lessons}/${c.lesson_count} bài hoàn thành</p><div class="track"><div class="bar" style="width:${c.progress_percent}%"></div></div></div><button class="btn btn-primary btn-small" data-course="${c.id}">Tiếp tục ↗</button></article>`).join('')}</div>`:'<div class="empty-state">Bạn chưa ghi danh khóa học nào.</div>'}`);bindCourseCards();}

async function renderMyFeedback(){const rows=await api('/api/student/feedback');shell(`<div class="section-toolbar"><div><span class="eyebrow">LỊCH SỬ CỦA BẠN</span><h3>Đánh giá đã gửi</h3></div></div>${rows.length?`<div class="review-list">${rows.map(r=>`<article class="review-card"><div class="review-top"><div><span class="eyebrow">${escapeHtml(r.course_title)}${r.lesson_title?' · '+escapeHtml(r.lesson_title):''}</span><div class="rating-stars">${'★'.repeat(r.rating)}<span>${'★'.repeat(5-r.rating)}</span></div></div><span class="sentiment-chip ${sentimentClasses[r.sentiment]}">${r.sentiment_label}</span></div><p>${escapeHtml(r.text)}</p><div class="review-bottom"><small>${new Date(r.created_at).toLocaleDateString('vi-VN')}</small><div><button class="text-button" data-edit="${r.id}">Sửa</button><button class="text-button danger-text" data-delete="${r.id}">Xóa</button></div></div></article>`).join('')}</div>`:'<div class="empty-state">Bạn chưa gửi đánh giá nào. Hoàn thành bài học để chia sẻ trải nghiệm.</div>'}`);
  $$('[data-edit]').forEach(b=>b.onclick=()=>{const row=rows.find(r=>r.id===Number(b.dataset.edit));openFeedbackModal(row.course_id,row.lesson_id,row)});
  $$('[data-delete]').forEach(b=>b.onclick=async()=>{if(!confirm('Xóa đánh giá này?'))return;try{await api(`/api/feedback/${b.dataset.delete}`,{method:'DELETE'});toast('Đã xóa đánh giá.');renderMyFeedback()}catch(e){toast(e.message,true)}});
}

async function renderProfile(){shell(`<section class="card-panel profile-panel"><span class="eyebrow">TÀI KHOẢN</span><h3>Hồ sơ cá nhân</h3><form id="profile-form" class="stack-form profile-form"><label>Họ và tên<input name="full_name" minlength="2" maxlength="120" value="${escapeHtml(me.full_name)}" required></label><label>Email<input value="${escapeHtml(me.email)}" disabled></label><button class="btn btn-primary">Lưu hồ sơ ↗</button></form><p class="muted small">Để đặt lại mật khẩu, hãy đăng xuất và chọn “Quên mật khẩu”.</p></section>`);$('#profile-form').onsubmit=async e=>{e.preventDefault();try{me=await api('/api/auth/profile',{method:'PATCH',body:JSON.stringify({full_name:new FormData(e.currentTarget).get('full_name')})});toast('Đã cập nhật hồ sơ.');renderProfile()}catch(err){toast(err.message,true)}};}

async function renderApp(){if(!token){renderAuth();return}try{me=await api('/api/auth/me')}catch{return}if(me.role==='admin'){location.href='/admin';return}try{if(currentCourse&&currentView==='detail')return openCourse(currentCourse.id);if(currentView==='learning')return await renderLearning();if(currentView==='reviews')return await renderMyFeedback();if(currentView==='profile')return renderProfile();currentView='catalog';await renderCatalog()}catch(err){app.innerHTML=`<main class="center-error"><div>Không tải được trang: ${escapeHtml(err.message)}</div><button class="btn btn-primary" onclick="location.reload()">Tải lại</button></main>`}}
function signOut(){token='';me=null;localStorage.removeItem(tokenKey);location.href='/'}

renderApp();
