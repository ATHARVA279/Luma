import React, { useEffect, useState } from 'react';
import { Zap, BarChart3, Clock, AlertCircle } from 'lucide-react';
import api from '../api/backend';
import Card from './ui/Card';
import Badge from './ui/Badge';
import Button from './ui/Button';

export default function UsageStats({ stats: propStats }) {
    const [stats, setStats] = useState(propStats);
    const [loading, setLoading] = useState(!propStats);

    useEffect(() => {
        if (propStats) {
            setStats(propStats);
            setLoading(false);
        } else {
            fetchStats();
        }
    }, [propStats]);

    const fetchStats = async () => {
        try {
            const res = await api.get('/auth/me');
            setStats(res.data);
        } catch (error) {
            console.error("Failed to fetch stats", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="animate-pulse h-20 bg-zinc-900/50 rounded-xl" />;

    if (!stats) return null;

    const credits = stats.credits || 0;
    const maxCredits = 100; // Hardcoded for free plan for now
    const percentage = Math.min(100, (credits / maxCredits) * 100);

    // Determine color based on percentage
    let color = "bg-emerald-500";
    if (percentage < 20) color = "bg-red-500";
    else if (percentage < 50) color = "bg-amber-500";

    return (
        <Card className="p-6 border-zinc-800 bg-zinc-900/30">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
                    <Zap className="w-5 h-5 text-yellow-400" fill="currentColor" />
                    Credits Balance
                </h3>
                <Badge variant={percentage < 20 ? "danger" : "default"}>
                    {credits} / {maxCredits}
                </Badge>
            </div>

            <div className="w-full bg-zinc-800 rounded-full h-2.5 mb-4 overflow-hidden">
                <div
                    className={`h-full rounded-full transition-all duration-500 ${color}`}
                    style={{ width: `${percentage}%` }}
                />
            </div>

            <div className="grid grid-cols-2 gap-4 mt-6">
                <div className="p-3 rounded-lg bg-zinc-900/50 border border-zinc-800">
                    <span className="text-xs text-zinc-500 block mb-1">Plan</span>
                    <span className="text-sm font-medium text-zinc-200 capitalize">{stats.plan || "Free"}</span>
                </div>
                <div className="p-3 rounded-lg bg-zinc-900/50 border border-zinc-800">
                    <span className="text-xs text-zinc-500 block mb-1">Resets In</span>
                    <span className="text-sm font-medium text-zinc-200">{stats.days_until_reset || 30} Days</span>
                </div>
            </div>

            {credits < 10 && (
                <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                    <p className="text-xs text-red-300">
                        You are running low on credits. Upgrade to Pro for unlimited access.
                    </p>
                </div>
            )}
        </Card>
    );
}
