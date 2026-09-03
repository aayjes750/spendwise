import React, { useState } from 'react';
import axios from 'axios';
import { DollarSign, Award, TrendingUp, CreditCard as CardIcon, ChevronDown, ChevronUp, Sparkles, ShieldCheck } from 'lucide-react';

const CATEGORIES = [
  { id: 'grocery', label: 'Groceries', defaultVal: 6000 },
  { id: 'dining', label: 'Dining & Restaurants', defaultVal: 3600 },
  { id: 'travel', label: 'Flights & Hotels', defaultVal: 2400 },
  { id: 'gas', label: 'Gas & Transit', defaultVal: 1800 },
  { id: 'streaming', label: 'Streaming & Entertainment', defaultVal: 600 },
  { id: 'catch_all', label: 'General / Other Spending', defaultVal: 4800 },
];

export default function App() {
  const [spending, setSpending] = useState(
    CATEGORIES.reduce((acc, cat) => ({ ...acc, [cat.id]: cat.defaultVal }), {})
  );
  // Modes: 'single' | 'wallet' | 'no-fee'
  const [mode, setMode] = useState('single');
  const [results, setResults] = useState([]);
  const [walletResult, setWalletResult] = useState(null);
  const [expandedCard, setExpandedCard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hasCalculated, setHasCalculated] = useState(false);

  const handleInputChange = (category, value) => {
    setSpending((prev) => ({
      ...prev,
      [category]: Math.max(0, Number(value) || 0),
    }));
  };

  const calculateOptimizedCards = async () => {
    setLoading(true);
    try {
      if (mode === 'single') {
        const response = await axios.post('https://spendwise-api-b5im.onrender.com/api/optimize', spending);
        setResults(response.data);
      } else if (mode === 'wallet') {
        const response = await axios.post('https://spendwise-api-b5im.onrender.com/api/optimize-wallet', spending);
        setWalletResult(response.data);
      } else if (mode === 'no-fee') {
        const response = await axios.post('https://spendwise-api-b5im.onrender.com/api/optimize-no-fee', spending);
        setResults(response.data);
      }
      setHasCalculated(true);
    } catch (err) {
      console.error('Calculation failed:', err);
      alert('Failed to connect to backend engine. Ensure FastAPI is running on Render.');
    } finally {
      setLoading(false);
    }
  };

  const totalAnnualSpend = Object.values(spending).reduce((sum, val) => sum + val, 0);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6 md:p-12 font-sans">
      <header className="max-w-6xl mx-auto mb-10 text-center">
        <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 px-4 py-1.5 rounded-full text-indigo-400 font-medium text-sm mb-3">
          <TrendingUp className="w-4 h-4" /> Algorithmic Reward Optimizer
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white mb-2">
          SpendWise
        </h1>
        <p className="text-slate-400 max-w-xl mx-auto text-base">
          Input your estimated annual budget to rank credit cards by mathematically validated Net Year 1 Value.
        </p>

        {/* 3-Way Mode Selector */}
        <div className="flex flex-wrap justify-center gap-3 mt-6">
          <button
            onClick={() => { setMode('single'); setHasCalculated(false); }}
            className={`px-5 py-2 rounded-xl font-semibold text-sm transition cursor-pointer ${
              mode === 'single'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'bg-slate-800 text-slate-400 hover:text-white border border-slate-700'
            }`}
          >
            Single Card Ranking
          </button>
          <button
            onClick={() => { setMode('wallet'); setHasCalculated(false); }}
            className={`px-5 py-2 rounded-xl font-semibold text-sm flex items-center gap-2 transition cursor-pointer ${
              mode === 'wallet'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'bg-slate-800 text-slate-400 hover:text-white border border-slate-700'
            }`}
          >
            <Sparkles className="w-4 h-4 text-amber-400" /> Optimal 2-Card Combo
          </button>
          <button
            onClick={() => { setMode('no-fee'); setHasCalculated(false); }}
            className={`px-5 py-2 rounded-xl font-semibold text-sm flex items-center gap-2 transition cursor-pointer ${
              mode === 'no-fee'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'bg-slate-800 text-slate-400 hover:text-white border border-slate-700'
            }`}
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400" /> No Annual Fee ($0)
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Spending Inputs Panel */}
        <section className="lg:col-span-5 bg-slate-800/60 border border-slate-700/60 rounded-2xl p-6 backdrop-blur-sm h-fit">
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-700">
            <h2 className="text-xl font-bold flex items-center gap-2 text-white">
              <DollarSign className="w-5 h-5 text-emerald-400" /> Annual Spend Profile
            </h2>
            <span className="text-xs bg-slate-700 text-slate-300 px-2.5 py-1 rounded-full font-mono">
              Total: ${totalAnnualSpend.toLocaleString()}/yr
            </span>
          </div>

          <div className="space-y-4">
            {CATEGORIES.map((cat) => (
              <div key={cat.id}>
                <div className="flex justify-between text-sm mb-1.5">
                  <label htmlFor={cat.id} className="text-slate-300 font-medium">{cat.label}</label>
                  <span className="text-emerald-400 font-mono">${spending[cat.id]?.toLocaleString()}</span>
                </div>
                <input
                  id={cat.id}
                  type="range"
                  min="0"
                  max="20000"
                  step="250"
                  value={spending[cat.id] || 0}
                  onChange={(e) => handleInputChange(cat.id, e.target.value)}
                  className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
              </div>
            ))}
          </div>

          <button
            onClick={calculateOptimizedCards}
            disabled={loading}
            className="w-full mt-8 py-3.5 px-4 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-semibold rounded-xl transition duration-150 flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/25 cursor-pointer"
          >
            {loading
              ? 'Evaluating Cards...'
              : mode === 'single'
              ? 'Calculate Optimal Cards'
              : mode === 'wallet'
              ? 'Find Best 2-Card Combo'
              : 'Find Best $0 Annual Fee Cards'}
          </button>
        </section>

        {/* Results Panel */}
        <section className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between pb-2">
            <h2 className="text-xl font-bold flex items-center gap-2 text-white">
              <Award className="w-5 h-5 text-amber-400" />
              {mode === 'single'
                ? 'Ranked Recommendations'
                : mode === 'wallet'
                ? 'Optimal 2-Card Wallet Pairing'
                : 'Top No-Annual-Fee Cards ($0 Fee)'}
            </h2>
          </div>

          {!hasCalculated ? (
            <div className="bg-slate-800/30 border border-dashed border-slate-700 rounded-2xl p-12 text-center text-slate-400">
              <CardIcon className="w-12 h-12 mx-auto mb-3 text-slate-600" />
              <p className="text-base font-medium">No calculation run yet</p>
              <p className="text-sm text-slate-500">Adjust your sliders and click calculate.</p>
            </div>
          ) : mode === 'wallet' && walletResult ? (
            <div className="space-y-4">
              <div className="bg-gradient-to-br from-indigo-950/40 via-slate-800/80 to-slate-800/80 border border-indigo-500/40 rounded-2xl p-6">
                <div className="flex justify-between items-center mb-4">
                  <span className="text-sm font-semibold uppercase tracking-wider text-indigo-400">Combined Value</span>
                  <span className="text-3xl font-black text-emerald-400 font-mono">${walletResult.total_net_value.toFixed(2)}</span>
                </div>
                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-700 text-sm">
                  <div>
                    <span className="text-slate-400 text-xs block">Optimal Card Pair</span>
                    <span className="font-bold text-white text-base">{walletResult.cards.map(c => c.card_name).join(' + ')}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-xs block">Combined Sign-Up Bonus</span>
                    <span className="font-bold text-emerald-400 text-base">+${walletResult.total_signup_bonus.toFixed(2)}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                {walletResult.cards.map((card, idx) => (
                  <div key={card.card_id} className="bg-slate-800/70 border border-slate-700 rounded-xl p-4">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-white">Card #{idx + 1}: {card.card_name}</span>
                      <span className="font-mono text-emerald-400 font-bold">${card.net_first_year_value.toFixed(2)} Net</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            results.map((card, idx) => {
              const isExpanded = expandedCard === card.card_name;
              return (
                <div
                  key={card.card_name}
                  className={`bg-slate-800/80 border rounded-2xl p-5 transition ${
                    idx === 0 ? 'border-amber-500/50 bg-gradient-to-r from-slate-800 to-amber-950/20' : 'border-slate-700/70'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono bg-slate-700 text-slate-300 px-2 py-0.5 rounded">
                          #{idx + 1}
                        </span>
                        <h3 className="text-lg font-bold text-white">{card.card_name}</h3>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-xs text-slate-400 uppercase tracking-wider block">Net Y1 Value</span>
                      <span className="text-2xl font-black text-emerald-400 font-mono">
                        ${card.net_first_year_value.toFixed(2)}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 bg-slate-900/60 rounded-xl p-3 text-xs border border-slate-800 mb-3">
                    <div>
                      <span className="text-slate-400 block">Spend Rewards</span>
                      <span className="font-semibold text-slate-200 font-mono">${card.annual_rewards.toFixed(2)}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Sign-Up Bonus</span>
                      <span className="font-semibold text-emerald-400 font-mono">
                        {card.signup_bonus_earned > 0 ? `+$${card.signup_bonus_earned.toFixed(2)}` : '$0.00'}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Effective Fee</span>
                      <span className="font-semibold text-rose-400 font-mono">-${card.effective_annual_fee.toFixed(2)}</span>
                    </div>
                  </div>

                  {/* Category Breakdown Accordion */}
                  <button
                    onClick={() => setExpandedCard(isExpanded ? null : card.card_name)}
                    className="w-full flex items-center justify-between text-xs text-slate-400 hover:text-slate-200 pt-2 border-t border-slate-700/50 cursor-pointer"
                  >
                    <span>{isExpanded ? 'Hide Category Breakdown' : 'View Reward Yield per Category'}</span>
                    {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>

                  {isExpanded && card.breakdown && (
                    <div className="mt-3 pt-3 border-t border-slate-700/50 grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                      {Object.entries(card.breakdown).map(([category, amount]) => (
                        <div key={category} className="bg-slate-900/40 rounded-lg p-2 border border-slate-800">
                          <span className="text-slate-400 capitalize block">{category.replace('_', ' ')}</span>
                          <span className="text-emerald-400 font-mono font-semibold">${amount.toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </section>
      </main>
    </div>
  );
}