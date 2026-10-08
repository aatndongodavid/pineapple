// frontend/src/features/community/ClassDashboardScreen.tsx

import React, { useState, useEffect } from 'react';
import { Megaphone, AlertTriangle, Vote, Calendar, Plus, CheckCircle2, ShieldAlert } from 'lucide-react';
import apiClient from '@/lib/api/client';
import { endpoints } from '@/lib/api/endpoints';
import { useAuthStore } from '@/lib/store/authStore';

interface Announcement {
  id: string;
  title: string;
  content: string;
  is_pinned: boolean;
  author_name: string;
  created_at: string;
}

interface Incident {
  id: string;
  category: string;
  title: string;
  description: string;
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED';
  created_at: string;
}

interface PollOption {
  id: string;
  text: string;
  vote_count: number;
}

interface Poll {
  id: string;
  question: string;
  options: PollOption[];
  is_closed: boolean;
  user_voted_option_id?: string;
}

interface Event {
  id: string;
  title: string;
  description?: string;
  event_date: string;
  kind: string;
}

export const ClassDashboardScreen: React.FC = () => {
  const { can, classGroup } = useAuthStore();
  const isDelegate = can('class.announce');

  const [tab, setTab] = useState<'ANNOUNCEMENTS' | 'INCIDENTS' | 'POLLS' | 'EVENTS'>('ANNOUNCEMENTS');
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [polls, setPolls] = useState<Poll[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);

  // Form states for delegate creation
  const [showModal, setShowModal] = useState(false);
  const [annTitle, setAnnTitle] = useState('');
  const [annContent, setAnnContent] = useState('');
  const [annPinned, setAnnPinned] = useState(false);

  const [incCategory, setIncCategory] = useState('TEACHER_ABSENT');
  const [incTitle, setIncTitle] = useState('');
  const [incDesc, setIncDesc] = useState('');

  const [pollQuestion, setPollQuestion] = useState('');
  const [pollOptionsInput, setPollOptionsInput] = useState('');

  const [evtTitle, setEvtTitle] = useState('');
  const [evtDate, setEvtDate] = useState('');
  const [evtKind, setEvtKind] = useState('EXAM');

  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const classGroupId = classGroup?.id || 'current';

  useEffect(() => {
    fetchTabData();
  }, [tab, classGroupId]);

  const fetchTabData = async () => {
    setLoading(true);
    try {
      if (tab === 'ANNOUNCEMENTS') {
        const res = await apiClient.get(endpoints.community.classAnnouncements(classGroupId));
        setAnnouncements(res.data.items || res.data || []);
      } else if (tab === 'INCIDENTS') {
        const res = await apiClient.get(endpoints.community.classIncidents(classGroupId));
        setIncidents(res.data.items || res.data || []);
      } else if (tab === 'POLLS') {
        const res = await apiClient.get(endpoints.community.classPolls(classGroupId));
        setPolls(res.data.items || res.data || []);
      } else if (tab === 'EVENTS') {
        const res = await apiClient.get(endpoints.community.classEvents(classGroupId));
        setEvents(res.data.items || res.data || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAnnouncement = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post(endpoints.community.classAnnouncements(classGroupId), {
        title: annTitle,
        content: annContent,
        is_pinned: annPinned,
      });
      setMessage({ type: 'success', text: 'Annonce publiée.' });
      setShowModal(false);
      setAnnTitle('');
      setAnnContent('');
      fetchTabData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.message || 'Erreur lors de la création.' });
    }
  };

  const handleReportIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post(endpoints.community.classIncidents(classGroupId), {
        category: incCategory,
        title: incTitle,
        description: incDesc,
      });
      setMessage({ type: 'success', text: 'Signalement transmis à la classe et à l\'administration.' });
      setShowModal(false);
      setIncTitle('');
      setIncDesc('');
      fetchTabData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.message || 'Erreur lors du signalement.' });
    }
  };

  const handleCreatePoll = async (e: React.FormEvent) => {
    e.preventDefault();
    const options = pollOptionsInput
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);
    if (options.length < 2) {
      setMessage({ type: 'error', text: 'Veuillez saisir au moins 2 choix.' });
      return;
    }
    try {
      await apiClient.post(endpoints.community.classPolls(classGroupId), {
        question: pollQuestion,
        options,
      });
      setMessage({ type: 'success', text: 'Sondage créé.' });
      setShowModal(false);
      setPollQuestion('');
      setPollOptionsInput('');
      fetchTabData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.message || 'Erreur de création.' });
    }
  };

  const handleVotePoll = async (pollId: string, optionId: string) => {
    try {
      await apiClient.post(`${endpoints.community.classPolls(classGroupId)}/${pollId}/vote`, {
        option_id: optionId,
      });
      setMessage({ type: 'success', text: 'Vote enregistré.' });
      fetchTabData();
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Impossible de voter.' });
    }
  };

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post(endpoints.community.classEvents(classGroupId), {
        title: evtTitle,
        event_date: evtDate,
        kind: evtKind,
      });
      setMessage({ type: 'success', text: 'Événement de classe ajouté.' });
      setShowModal(false);
      setEvtTitle('');
      setEvtDate('');
      fetchTabData();
    } catch (err: any) {
      setMessage({ type: 'error', text: 'Erreur lors de la création.' });
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 p-4 md:p-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
            <Megaphone className="h-7 w-7 text-pineapple" />
            Espace Classe : {classGroup?.name || 'Ma Classe'}
          </h1>
          <p className="text-sm text-gray-500">
            Annonces, signalements d'incidents, sondages et calendrier de votre promotion.
          </p>
        </div>

        {isDelegate && (
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2.5 bg-pineapple hover:bg-pineapple-hover text-white text-sm font-semibold rounded-xl shadow-md transition flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Nouveau ({tab.toLowerCase()})
          </button>
        )}
      </div>

      {message && (
        <div
          className={`p-4 rounded-xl text-sm font-medium flex items-center gap-2 ${
            message.type === 'success'
              ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20'
              : 'bg-rose-500/10 text-rose-600 border border-rose-500/20'
          }`}
        >
          {message.type === 'success' ? <CheckCircle2 className="h-5 w-5" /> : <ShieldAlert className="h-5 w-5" />}
          {message.text}
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-gray-200 dark:border-slate-700 pb-2">
        {[
          { id: 'ANNOUNCEMENTS', label: 'Annonces', icon: Megaphone },
          { id: 'INCIDENTS', label: 'Signalements', icon: AlertTriangle },
          { id: 'POLLS', label: 'Sondages', icon: Vote },
          { id: 'EVENTS', label: 'Calendrier', icon: Calendar },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id as any)}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
              tab === t.id
                ? 'bg-pineapple text-white shadow-sm'
                : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-slate-800'
            }`}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="space-y-4">
        {loading ? (
          <div className="p-12 text-center text-gray-400 text-sm">Chargement...</div>
        ) : tab === 'ANNOUNCEMENTS' ? (
          announcements.length === 0 ? (
            <div className="p-12 text-center text-gray-400 text-sm">Aucune annonce pour le moment.</div>
          ) : (
            announcements.map((a) => (
              <div
                key={a.id}
                className={`p-6 bg-white dark:bg-slate-800 rounded-2xl border shadow-sm space-y-2 ${
                  a.is_pinned ? 'border-pineapple border-2' : 'border-gray-100 dark:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-lg text-gray-800 dark:text-white">{a.title}</h3>
                  {a.is_pinned && (
                    <span className="px-2.5 py-0.5 bg-pineapple/15 text-pineapple text-[10px] font-bold uppercase rounded-full">
                      Épinglé
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300">{a.content}</p>
                <p className="text-xs text-gray-400 pt-2 border-t border-gray-100 dark:border-slate-700">
                  Par {a.author_name || 'Délégué'} • {new Date(a.created_at).toLocaleDateString('fr-FR')}
                </p>
              </div>
            ))
          )
        ) : tab === 'INCIDENTS' ? (
          incidents.length === 0 ? (
            <div className="p-12 text-center text-gray-400 text-sm">Aucun incident signalé.</div>
          ) : (
            incidents.map((inc) => (
              <div
                key={inc.id}
                className="p-5 bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 shadow-sm flex items-start justify-between"
              >
                <div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-500/10 text-amber-600 mb-2 inline-block">
                    {inc.category}
                  </span>
                  <h3 className="font-bold text-base text-gray-800 dark:text-white">{inc.title}</h3>
                  <p className="text-xs text-gray-500 mt-1">{inc.description}</p>
                </div>
                <span
                  className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase ${
                    inc.status === 'RESOLVED'
                      ? 'bg-emerald-500/10 text-emerald-600'
                      : 'bg-amber-500/10 text-amber-600'
                  }`}
                >
                  {inc.status}
                </span>
              </div>
            ))
          )
        ) : tab === 'POLLS' ? (
          polls.length === 0 ? (
            <div className="p-12 text-center text-gray-400 text-sm">Aucun sondage actif.</div>
          ) : (
            polls.map((p) => (
              <div
                key={p.id}
                className="p-6 bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 shadow-sm space-y-4"
              >
                <h3 className="font-bold text-base text-gray-800 dark:text-white">{p.question}</h3>
                <div className="space-y-2">
                  {p.options.map((opt) => (
                    <button
                      key={opt.id}
                      onClick={() => handleVotePoll(p.id, opt.id)}
                      disabled={p.is_closed}
                      className={`w-full p-3 rounded-xl border text-left text-sm font-medium transition flex items-center justify-between ${
                        p.user_voted_option_id === opt.id
                          ? 'bg-pineapple/15 border-pineapple text-pineapple'
                          : 'border-gray-200 dark:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-700/50'
                      }`}
                    >
                      <span>{opt.text}</span>
                      <span className="text-xs text-gray-400 font-bold">{opt.vote_count} votes</span>
                    </button>
                  ))}
                </div>
              </div>
            ))
          )
        ) : events.length === 0 ? (
          <div className="p-12 text-center text-gray-400 text-sm">Aucun événement programmé.</div>
        ) : (
          events.map((evt) => (
            <div
              key={evt.id}
              className="p-5 bg-white dark:bg-slate-800 rounded-2xl border border-gray-100 dark:border-slate-700 shadow-sm flex items-center justify-between"
            >
              <div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-blue-500/10 text-blue-600 mb-1 inline-block">
                  {evt.kind}
                </span>
                <h3 className="font-bold text-base text-gray-800 dark:text-white">{evt.title}</h3>
              </div>
              <p className="text-sm font-bold text-pineapple">
                {new Date(evt.event_date).toLocaleDateString('fr-FR')}
              </p>
            </div>
          ))
        )}
      </div>

      {/* Modal création délégué */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h2 className="text-lg font-bold text-gray-800 dark:text-white">
              Nouveau contenu : {tab}
            </h2>

            {tab === 'ANNOUNCEMENTS' && (
              <form onSubmit={handleCreateAnnouncement} className="space-y-4 text-sm">
                <input
                  type="text"
                  placeholder="Titre de l'annonce"
                  value={annTitle}
                  onChange={(e) => setAnnTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900"
                  required
                />
                <textarea
                  placeholder="Contenu..."
                  value={annContent}
                  onChange={(e) => setAnnContent(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900"
                  required
                />
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={annPinned}
                    onChange={(e) => setAnnPinned(e.target.checked)}
                    className="text-pineapple focus:ring-pineapple"
                  />
                  <span>Épingler cette annonce</span>
                </label>
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 text-xs font-semibold text-gray-500"
                  >
                    Annuler
                  </button>
                  <button type="submit" className="px-4 py-2 bg-pineapple text-white text-xs font-semibold rounded-xl">
                    Publier
                  </button>
                </div>
              </form>
            )}

            {tab === 'INCIDENTS' && (
              <form onSubmit={handleReportIncident} className="space-y-4 text-sm">
                <select
                  value={incCategory}
                  onChange={(e) => setIncCategory(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900"
                >
                  <option value="TEACHER_ABSENT">Enseignant absent</option>
                  <option value="CLASS_CANCELLED">Cours annulé</option>
                  <option value="ROOM_EQUIPMENT">Problème de salle/matériel</option>
                  <option value="REQUEST">Demande à l'administration</option>
                </select>
                <input
                  type="text"
                  placeholder="Objet du signalement"
                  value={incTitle}
                  onChange={(e) => setIncTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900"
                  required
                />
                <textarea
                  placeholder="Détails..."
                  value={incDesc}
                  onChange={(e) => setIncDesc(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900"
                  required
                />
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 text-xs font-semibold text-gray-500"
                  >
                    Annuler
                  </button>
                  <button type="submit" className="px-4 py-2 bg-amber-500 text-white text-xs font-semibold rounded-xl">
                    Signaler
                  </button>
                </div>
              </form>
            )}

            {tab === 'POLLS' && (
              <form onSubmit={handleCreatePoll} className="space-y-4 text-sm">
                <input
                  type="text"
                  placeholder="Question du sondage"
                  value={pollQuestion}
                  onChange={(e) => setPollQuestion(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900"
                  required
                />
                <textarea
                  placeholder="Un choix par ligne..."
                  value={pollOptionsInput}
                  onChange={(e) => setPollOptionsInput(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900 font-mono text-xs"
                  required
                />
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 text-xs font-semibold text-gray-500"
                  >
                    Annuler
                  </button>
                  <button type="submit" className="px-4 py-2 bg-pineapple text-white text-xs font-semibold rounded-xl">
                    Créer le sondage
                  </button>
                </div>
              </form>
            )}

            {tab === 'EVENTS' && (
              <form onSubmit={handleCreateEvent} className="space-y-4 text-sm">
                <input
                  type="text"
                  placeholder="Titre de l'événement / examen"
                  value={evtTitle}
                  onChange={(e) => setEvtTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900"
                  required
                />
                <input
                  type="date"
                  value={evtDate}
                  onChange={(e) => setEvtDate(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900"
                  required
                />
                <select
                  value={evtKind}
                  onChange={(e) => setEvtKind(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-900"
                >
                  <option value="EXAM">Examen / Contrôle</option>
                  <option value="DEADLINE">Projet / Devoir à rendre</option>
                  <option value="MEETING">Réunion / Rassemblement</option>
                </select>
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 text-xs font-semibold text-gray-500"
                  >
                    Annuler
                  </button>
                  <button type="submit" className="px-4 py-2 bg-pineapple text-white text-xs font-semibold rounded-xl">
                    Ajouter au calendrier
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
