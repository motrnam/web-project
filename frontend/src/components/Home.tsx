// frontend/src/pages/Home.tsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';

const Home = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    total_solved_cases: 0,
    total_employees: 0,
    active_cases: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('/api/case/stats/');
        const data = await response.json();
        setStats(data);
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900">

      {/* Header */}
      <header className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-950 via-blue-900 to-slate-900" />
        <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

        <div className="relative max-w-7xl mx-auto px-6 py-28 text-center">
          <h1 className="text-4xl md:text-6xl font-extrabold text-white mb-6 leading-tight tracking-tight">
            سامانه مدیریت پرونده‌های جنایی
          </h1>

          <p className="text-lg md:text-2xl text-blue-100/90 max-w-3xl mx-auto mb-10">
            اداره پلیس شهر لس‌آنجلس – مدیریت هوشمند پرونده‌ها، شواهد و پیگیری‌ها
          </p>

          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Link
              to="/login"
              className="px-8 py-4 rounded-xl bg-white text-blue-900 font-semibold shadow-xl hover:shadow-2xl hover:scale-[1.03] transition"
            >
              ورود به سامانه
            </Link>
          </div>

        <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Link
              to="/register"
              className="px-8 py-4 rounded-xl border border-white/60 text-white font-semibold hover:bg-white/10 transition"
            >
              ثبت‌نام
            </Link>
          </div>

        </div>
      </header>

      {/* About */}
      <section className="py-20 px-4 max-w-7xl mx-auto">
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl rounded-3xl shadow-2xl p-10 md:p-14 border border-gray-200/50 dark:border-gray-700">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-6">
            درباره سامانه
          </h2>
          <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed text-center max-w-4xl mx-auto">
            این سامانه با هدف دیجیتال‌سازی فرآیند مدیریت پرونده‌های جنایی طراحی شده است. نیروهای پلیس می‌توانند پرونده‌ها، شواهد، مظنونین و گزارش‌ها را به‌صورت یکپارچه مدیریت کرده و روند پیگیری را تسریع کنند.
          </p>
        </div>
      </section>

      {/* Stats */}
      <section className="py-20 px-4 bg-white dark:bg-gray-950">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">
            آمار سامانه
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                title: 'پرونده‌های حل شده',
                value: stats.total_solved_cases,
                color: 'text-blue-600'
              },
              {
                title: 'کارمندان فعال',
                value: stats.total_employees,
                color: 'text-green-600'
              },
              {
                title: 'پرونده‌های فعال',
                value: stats.active_cases,
                color: 'text-yellow-500'
              }
            ].map((item, i) => (
              <div
                key={i}
                className="relative bg-white dark:bg-gray-900 rounded-2xl p-8 shadow-lg border border-gray-200 dark:border-gray-700 hover:shadow-2xl transition-all"
              >
                <p className="text-sm text-gray-500 mb-2">
                  {item.title}
                </p>
                <h3 className={`text-4xl font-extrabold ${item.color}`}>
                  {loading ? '...' : item.value.toLocaleString()}
                </h3>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 bg-gradient-to-br from-indigo-950 via-blue-900 to-slate-900 text-white text-center">
        <h2 className="text-3xl md:text-5xl font-extrabold mb-6">
          آماده ورود به سامانه هستید؟
        </h2>
        <p className="text-lg md:text-xl opacity-80 max-w-2xl mx-auto mb-10">
          همین حالا وارد شوید و فرآیند مدیریت پرونده‌ها را به‌صورت دیجیتال تجربه کنید.
        </p>

        <Link
          to="/login"
          className="inline-flex items-center gap-2 px-10 py-4 bg-white text-blue-900 rounded-xl font-bold shadow-xl hover:scale-105 transition"
        >
          ورود به سامانه
        </Link>
      </section>

    </div>
  );
};

export default Home;