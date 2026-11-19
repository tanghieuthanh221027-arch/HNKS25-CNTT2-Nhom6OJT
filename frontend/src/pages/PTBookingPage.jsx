import { useMemo, useState } from "react";
import { Link } from "react-router-dom";


const ptBookingStyles = `
.pt-booking-page {
  --pt-bg: #0b1326;
  --pt-surface: #131b2e;
  --pt-card: #171f33;
  --pt-text: #e3e9f7;
  --pt-muted: #9ca8bf;
  --pt-accent: #ff9b62;
  min-height: 100vh;
  background: radial-gradient(ellipse at 15% 0%, rgb(249 115 22 / 9%), transparent 34%), var(--pt-bg);
  color: var(--pt-text);
  font-family: Inter, Arial, sans-serif;
}

.pt-booking-page *,
.pt-booking-page *::before,
.pt-booking-page *::after {
  box-sizing: border-box;
}

.pt-booking-page button,
.pt-booking-page a {
  font: inherit;
}

.pt-booking-page a {
  color: inherit;
  text-decoration: none;
}

.pt-booking-page .material-symbols-outlined {
  line-height: 1;
}

.pt-booking-header {
  height: 76px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 max(22px, calc((100vw - 1240px) / 2));
  border-bottom: 1px solid rgb(255 255 255 / 7%);
  background: rgb(11 19 38 / 88%);
}

.pt-booking-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pt-booking-brand>.material-symbols-outlined {
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  border-radius: 9px;
  background: var(--pt-accent);
  color: #281609;
}

.pt-booking-brand b,
.pt-booking-brand small {
  display: block;
}

.pt-booking-brand b {
  font-family: "Space Grotesk", Inter, sans-serif;
  font-size: 14px;
  letter-spacing: .1em;
}

.pt-booking-brand small {
  margin-top: 4px;
  color: var(--pt-muted);
  font-size: 9px;
  letter-spacing: .14em;
}

.pt-back-link {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--pt-muted) !important;
  font-size: 13px !important;
}

.pt-back-link:hover {
  color: var(--pt-accent) !important;
}

.pt-back-link .material-symbols-outlined {
  font-size: 19px;
}

.pt-booking-content {
  width: min(1240px, 100%);
  margin: 0 auto;
  padding: 52px 24px 80px;
}

.pt-booking-title {
  margin-bottom: 42px;
}

.pt-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--pt-accent);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .15em;
}

.pt-eyebrow .material-symbols-outlined {
  font-size: 16px;
}

.pt-booking-title h1 {
  margin: 12px 0 8px;
  font: 700 clamp(30px, 5vw, 46px)/1.1 "Space Grotesk", Inter, sans-serif;
  letter-spacing: -.04em;
}

.pt-booking-title h1 span {
  color: var(--pt-accent);
}

.pt-booking-title p {
  margin: 0;
  color: var(--pt-muted);
  font-size: 14px;
}

.pt-booking-section {
  margin-top: 32px;
}

.pt-section-heading {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 18px;
}

.pt-section-heading>span {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  border: 1px solid rgb(255 155 98 / 35%);
  border-radius: 9px;
  color: var(--pt-accent);
  font-size: 12px;
  font-weight: 700;
}

.pt-section-heading h2 {
  margin: 0;
  font: 600 18px "Space Grotesk", Inter, sans-serif;
}

.pt-section-heading p {
  margin: 5px 0 0;
  color: var(--pt-muted);
  font-size: 12px;
}

.pt-trainer-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.pt-trainer-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
  padding: 16px;
  border: 1px solid rgb(255 255 255 / 7%);
  border-radius: 12px;
  background: var(--pt-surface);
  color: var(--pt-text);
  cursor: pointer;
  text-align: left;
  transition: border-color .18s, transform .18s, background .18s;
}

.pt-trainer-card:hover {
  transform: translateY(-2px);
  background: var(--pt-card);
}

.pt-trainer-card.is-selected {
  border-color: var(--pt-accent);
  box-shadow: 0 0 0 1px rgb(255 155 98 / 30%);
}

.pt-trainer-card img {
  width: 64px;
  height: 64px;
  flex: 0 0 auto;
  border-radius: 10px;
  object-fit: cover;
  background: #273148;
}

.pt-trainer-info {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 6px;
}

.pt-trainer-info>b {
  font-size: 14px;
}

.pt-trainer-info>small {
  overflow: hidden;
  color: var(--pt-muted);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pt-rating {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #ffc878;
  font-size: 11px;
}

.pt-rating .material-symbols-outlined {
  font-size: 15px;
}

.pt-exp {
  overflow: hidden;
  color: var(--pt-muted);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pt-selected-mark {
  position: absolute;
  top: 11px;
  right: 11px;
  color: var(--pt-accent);
  font-size: 19px;
}

.pt-week-controls {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 12px;
  padding: 11px 14px;
  border: 1px solid rgb(255 255 255 / 6%);
  border-radius: 10px;
  background: var(--pt-surface);
}

.pt-week-arrows {
  display: flex;
  align-items: center;
  padding: 3px;
  border-radius: 7px;
  background: #0d1527;
}

.pt-week-arrows button {
  display: inline-grid;
  min-width: 34px;
  height: 30px;
  place-items: center;
  border: 0;
  border-radius: 5px;
  background: transparent;
  color: var(--pt-text);
  cursor: pointer;
}

.pt-week-arrows button:hover {
  background: #222d43;
}

.pt-week-arrows .pt-today-button {
  padding: 0 9px;
  font-size: 11px;
}

.pt-week-label {
  color: var(--pt-text);
  font-size: 12px;
  font-weight: 600;
}

.pt-selected-trainer {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  color: var(--pt-muted);
  font-size: 11px;
}

.pt-selected-trainer .material-symbols-outlined {
  color: var(--pt-accent);
  font-size: 17px;
}

.pt-calendar {
  display: grid;
  grid-template-columns: repeat(7, minmax(130px, 1fr));
  overflow-x: auto;
  border: 1px solid rgb(255 255 255 / 7%);
  border-radius: 11px;
  background: var(--pt-surface);
}

.pt-calendar-day {
  min-width: 130px;
  border-right: 1px solid rgb(255 255 255 / 6%);
}

.pt-calendar-day:last-child {
  border: 0;
}

.pt-day-heading {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 12px 10px;
  border-bottom: 1px solid rgb(255 255 255 / 7%);
  text-align: center;
}

.pt-day-heading b {
  font-size: 10px;
}

.pt-day-heading span {
  color: var(--pt-muted);
  font-size: 10px;
}

.pt-slots {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px;
}

.pt-slot {
  display: flex;
  min-height: 43px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  border: 1px solid rgb(98 214 160 / 15%);
  border-radius: 6px;
  background: rgb(98 214 160 / 7%);
  color: #8ce0b8;
  cursor: pointer;
  font-size: 11px;
  font-weight: 700;
}

.pt-slot small {
  font-size: 8px;
  font-weight: 400;
}

.pt-slot:not(:disabled):hover {
  border-color: #62d6a0;
  background: rgb(98 214 160 / 16%);
}

.pt-slot.is-selected {
  border-color: var(--pt-accent);
  background: rgb(255 155 98 / 20%);
  color: #ffc4a2;
}

.pt-slot.is-unavailable {
  border-color: rgb(255 255 255 / 4%);
  background: rgb(255 255 255 / 3%);
  color: #68738b;
  cursor: not-allowed;
}

.pt-availability-note {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: 12px;
  color: var(--pt-muted);
  font-size: 10px;
}

.pt-dot {
  width: 7px;
  height: 7px;
  margin-left: 12px;
  border-radius: 50%;
  background: #62d6a0;
}

.pt-dot:first-child {
  margin-left: 0;
}

.pt-dot-full {
  background: #68738b;
}

.pt-dot-selected {
  background: var(--pt-accent);
}

.pt-confirm-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-top: 24px;
  padding: 18px;
  border: 1px solid rgb(255 255 255 / 7%);
  border-radius: 11px;
  background: linear-gradient(105deg, rgb(255 155 98 / 8%), var(--pt-surface) 60%);
}

.pt-confirm-card>div {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.pt-confirm-card>div>.material-symbols-outlined {
  color: var(--pt-accent);
  font-size: 22px;
}

.pt-confirm-card b,
.pt-confirm-card small {
  display: block;
}

.pt-confirm-card b {
  font-size: 12px;
}

.pt-confirm-card small {
  margin-top: 5px;
  color: var(--pt-muted);
  font-size: 10px;
}

.pt-confirm-button {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 0 15px;
  border: 0;
  border-radius: 6px;
  background: var(--pt-accent);
  color: #291406;
  cursor: pointer;
  font-size: 11px !important;
  font-weight: 700 !important;
}

.pt-confirm-button:disabled {
  background: #344056;
  color: #8590a6;
  cursor: not-allowed;
}

.pt-confirm-button .material-symbols-outlined {
  font-size: 17px;
}

.pt-booking-notice {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 12px 0 0;
  color: #9ddcbd;
  font-size: 12px;
  line-height: 1.5;
}

.pt-booking-notice .material-symbols-outlined {
  flex: 0 0 auto;
  font-size: 18px;
}

@media (max-width: 800px) {
  .pt-trainer-grid {
    grid-template-columns: 1fr;
  }

  .pt-trainer-card {
    padding: 13px;
  }

  .pt-week-controls {
    flex-wrap: wrap;
  }

  .pt-selected-trainer {
    margin-left: 0;
  }
}

@media (max-width: 520px) {
  .pt-booking-header {
    height: 66px;
    padding: 0 16px;
  }

  .pt-booking-content {
    padding: 34px 16px 54px;
  }

  .pt-booking-title {
    margin-bottom: 32px;
  }

  .pt-section-heading h2 {
    font-size: 16px;
  }

  .pt-confirm-card {
    align-items: stretch;
    flex-direction: column;
  }

  .pt-confirm-button {
    justify-content: center;
  }

  .pt-week-label {
    width: calc(100% - 8px);
  }
}

`;
const trainers = [
  { id: 1, name: "Tráº§n HÃ¹ng SÆ¡n", focus: "TÄƒng cÆ¡ & thá»ƒ hÃ¬nh", rating: "4.9", experience: "6 nÄƒm kinh nghiá»‡m", image: "https://lh3.googleusercontent.com/aida-public/AB6AXuDBbz9xXFmNxAk5ybAPEV7oFsHEO1T8isc_LHtDDWKidJ_6CDm9pYjBHQl9AzKijwB5XnepTY_z_NRKBdRQoawko5L3sbnezJ_S4CgC5VLd3vnb2lS3Hr4GmPlu4yPGZNiD-aYM90rUfNCHkbaBUS-B6mJHFrpUJPaUyCCvwz3uzSM5YiI92p1h4prMPAOS8MGkKKhdb6F2jboAEIusDlvq5QOSWelQcbYN-v-lvlM" },
  { id: 2, name: "LÃª HoÃ ng Yáº¿n", focus: "Giáº£m má»¡ & Kickfit", rating: "4.8", experience: "4 nÄƒm kinh nghiá»‡m", image: "https://lh3.googleusercontent.com/aida-public/AB6AXuC4ERcrirpbKucvY855mYsVsQk10iz40-iciSn96QHGwEzt6Xq3fhSqklz5U4eCsZznC0jy9U5aOWQ_dUVESEkA-YGp_eALkzrPVvMVGk0kf_tlIXKrTZCGb_7atZN7BeKuOhABnYEQvKEEjIThWVB-V6crEr8K2TyFSqdMa9v_zn-ItpJkCAg8p3eT6qk5sN8f--BO2yjLadVi6zVzeF6SQoiX5jr22b92ne9A6lw" },
  { id: 3, name: "VÅ© Minh Tuáº¥n", focus: "Phá»¥c há»“i & Yoga", rating: "5.0", experience: "5 nÄƒm kinh nghiá»‡m", image: "https://lh3.googleusercontent.com/aida-public/AB6AXuCy-5-Ff_wFo6CRQk_nZhIoP6AnorGBmPWFdB2hwvr05gYJ7aEOIAO2WZLN__6tSHcOD4mAD6IbblC-QFM4MI-Wrc3M2XOx206ttp1P_sMS3OEwhcNopYG9q_7WJsc6covbZqWc8Zurq3Bsnorw7u7Zig8BjI-vX9EGUv_u3-YKajkOQEJPStg8BWimmNGEjt9yHfeB0xFvJbX-SJiUQnbs9RbwZ5w5MeSCsqnqzV0" },
];

const timeSlots = ["06:00", "07:00", "08:00", "09:00", "14:00", "15:00", "16:00", "17:00"];
const dayNames = ["Thá»© Hai", "Thá»© Ba", "Thá»© TÆ°", "Thá»© NÄƒm", "Thá»© SÃ¡u", "Thá»© Báº£y", "Chá»§ Nháº­t"];

function getWeekDays(offset) {
  const today = new Date();
  const monday = new Date(today);
  const day = (today.getDay() + 6) % 7;
  monday.setDate(today.getDate() - day + offset * 7);
  return dayNames.map((name, index) => {
    const date = new Date(monday);
    date.setDate(monday.getDate() + index);
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
    return { name, date, key };
  });
}

export default function PTBookingPage() {
  const [trainerId, setTrainerId] = useState(trainers[0].id);
  const [weekOffset, setWeekOffset] = useState(0);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [notice, setNotice] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const days = useMemo(() => getWeekDays(weekOffset), [weekOffset]);
  const selectedTrainer = trainers.find((trainer) => trainer.id === trainerId);

  const chooseSlot = (day, time) => {
    setNotice("");
    setConfirmed(false);
    setSelectedSlot({ day, time });
  };

  const confirmBooking = () => {
    setConfirmed(true);
    setNotice("ÄÃ£ ghi nháº­n lá»±a chá»n cá»§a báº¡n. Vui lÃ²ng liÃªn há»‡ quáº§y lá»… tÃ¢n Ä‘á»ƒ hoÃ n táº¥t xÃ¡c nháº­n lá»‹ch.");
  };

  return (
    <div className="pt-booking-page">
      <style>{ptBookingStyles}</style>
      <header className="pt-booking-header">
        <Link to="/member" className="pt-booking-brand"><span className="material-symbols-outlined">fitness_center</span><span><b>DUCKY GYM</b><small>PERFORMANCE CLUB</small></span></Link>
        <Link className="pt-back-link" to="/member"><span className="material-symbols-outlined">arrow_back</span>Trang há»™i viÃªn</Link>
      </header>
      <main className="pt-booking-content">
        <div className="pt-booking-title">
          <span className="pt-eyebrow"><span className="material-symbols-outlined">event_available</span> Äáº¶T Lá»ŠCH CÃ NHÃ‚N</span>
          <h1>Äáº·t lá»‹ch táº­p vá»›i <span>PT</span></h1>
          <p>Chá»n huáº¥n luyá»‡n viÃªn vÃ  khung giá» phÃ¹ há»£p vá»›i lá»‹ch cá»§a báº¡n.</p>
        </div>

        <section className="pt-booking-section" aria-labelledby="trainer-heading">
          <div className="pt-section-heading"><span>01</span><div><h2 id="trainer-heading">Chá»n huáº¥n luyá»‡n viÃªn</h2><p>Chá»n PT phÃ¹ há»£p vá»›i má»¥c tiÃªu táº­p luyá»‡n cá»§a báº¡n.</p></div></div>
          <div className="pt-trainer-grid">
            {trainers.map((trainer) => (
              <button type="button" key={trainer.id} className={`pt-trainer-card ${trainerId === trainer.id ? "is-selected" : ""}`} onClick={() => setTrainerId(trainer.id)} aria-pressed={trainerId === trainer.id}>
                <img src={trainer.image} alt={`Huáº¥n luyá»‡n viÃªn ${trainer.name}`} />
                <span className="pt-trainer-info"><b>{trainer.name}</b><small>{trainer.focus}</small><span className="pt-rating"><span className="material-symbols-outlined">star</span> {trainer.rating} <span className="pt-exp">Â· {trainer.experience}</span></span></span>
                {trainerId === trainer.id && <span className="pt-selected-mark material-symbols-outlined">check_circle</span>}
              </button>
            ))}
          </div>
        </section>

        <section className="pt-booking-section" aria-labelledby="schedule-heading">
          <div className="pt-section-heading"><span>02</span><div><h2 id="schedule-heading">Chá»n ngÃ y vÃ  giá»</h2><p>Lá»‹ch trá»‘ng minh há»a, vui lÃ²ng xÃ¡c nháº­n táº¡i quáº§y.</p></div></div>
          <div className="pt-week-controls">
            <div className="pt-week-arrows"><button type="button" onClick={() => { setWeekOffset((value) => value - 1); setSelectedSlot(null); }} aria-label="Tuáº§n trÆ°á»›c"><span className="material-symbols-outlined">chevron_left</span></button><button type="button" onClick={() => { setWeekOffset(0); setSelectedSlot(null); }} className="pt-today-button">Tuáº§n nÃ y</button><button type="button" onClick={() => { setWeekOffset((value) => value + 1); setSelectedSlot(null); }} aria-label="Tuáº§n sau"><span className="material-symbols-outlined">chevron_right</span></button></div>
            <span className="pt-week-label">{days[0].date.toLocaleDateString("vi-VN")} â€“ {days[6].date.toLocaleDateString("vi-VN")}</span>
            <span className="pt-selected-trainer"><span className="material-symbols-outlined">person</span>{selectedTrainer.name}</span>
          </div>
          <div className="pt-calendar">
            {days.map((day, dayIndex) => (
              <div className="pt-calendar-day" key={day.key}>
                <div className="pt-day-heading"><b>{day.name}</b><span>{day.date.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" })}</span></div>
                <div className="pt-slots">
                  {timeSlots.map((time, slotIndex) => {
                    const isUnavailable = (dayIndex + slotIndex + trainerId) % 7 === 0;
                    const isSelected = selectedSlot?.day.key === day.key && selectedSlot?.time === time;
                    return <button type="button" key={time} disabled={isUnavailable} className={`pt-slot ${isUnavailable ? "is-unavailable" : ""} ${isSelected ? "is-selected" : ""}`} onClick={() => chooseSlot(day, time)}>{time}<small>{isUnavailable ? "ÄÃ£ kÃ­n" : "CÃ²n trá»‘ng"}</small></button>;
                  })}
                </div>
              </div>
            ))}
          </div>
          <div className="pt-availability-note"><span className="pt-dot pt-dot-open" /> CÃ²n trá»‘ng <span className="pt-dot pt-dot-full" /> ÄÃ£ kÃ­n <span className="pt-dot pt-dot-selected" /> Äang chá»n</div>
        </section>

        <section className="pt-confirm-card">
          <div><span className="material-symbols-outlined">calendar_month</span><div><b>{selectedSlot ? `${selectedSlot.day.name}, ${selectedSlot.day.date.toLocaleDateString("vi-VN")} Â· ${selectedSlot.time} â€“ ${String(Number(selectedSlot.time.slice(0, 2)) + 1).padStart(2, "0")}:00` : "ChÆ°a chá»n khung giá»"}</b><small>{selectedSlot ? `${selectedTrainer.name} Â· ${selectedTrainer.focus}` : "Chá»n má»™t giá» cÃ²n trá»‘ng trong lá»‹ch phÃ­a trÃªn"}</small></div></div>
          <button type="button" className="pt-confirm-button" disabled={!selectedSlot || confirmed} onClick={confirmBooking}>{confirmed ? "ÄÃ£ ghi nháº­n" : "XÃ¡c nháº­n lá»±a chá»n"}<span className="material-symbols-outlined">arrow_forward</span></button>
        </section>
        {notice && <p className="pt-booking-notice" role="status"><span className="material-symbols-outlined">info</span>{notice}</p>}
      </main>
    </div>
  );
}

