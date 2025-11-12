"""
Risk Analysis Agent - 风险分析Agent
审核交易决策的风险，包括仓位大小、回撤风险、组合风险
创建时间: 2025-11-12
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal

from .state import TradingState
from ..utils.constants import TradingAction, RiskLevel
from ..exchanges.factory import get_trader
from ..utils.logging import get_logger

logger = get_logger(__name__)


class RiskAnalyzer:
    """风险分析器"""
    
    def __init__(self, session_id: int, risk_params: Dict[str, Any]):
        """
        初始化风险分析器
        
        Args:
            session_id: 会话ID
            risk_params: 风险参数配置
        """
        self.session_id = session_id
        self.risk_params = risk_params
        self.trader = get_trader(session_id=session_id)
        
        # 从风险参数中提取关键配置
        self.max_position_per_trade = risk_params.get("max_position_per_trade", 1000)
        self.max_drawdown_pct = risk_params.get("max_drawdown_pct", 10.0)
        self.max_total_exposure = risk_params.get("max_total_exposure", 5000)
        self.max_positions = risk_params.get("max_positions", 3)
        self.max_leverage = risk_params.get("max_leverage", 10)
    
    async def analyze_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析单个决策的风险
        
        Args:
            decision: 决策字典
            
        Returns:
            风险分析结果
        """
        symbol = decision['symbol']
        action = decision['action']
        
        risk_result = {
            'symbol': symbol,
            'action': action,
            'approved': True,
            'warnings': [],
            'adjustments': {},
            'risk_metrics': {}
        }
        
        # 对于非开仓操作，直接通过
        if action not in TradingAction.OPEN_ACTIONS:
            risk_result['risk_metrics']['risk_level'] = RiskLevel.LOW
            return risk_result
        
        # 1. 审核仓位大小
        position_size = decision.get('position_size_usd', 0)
        leverage = decision.get('leverage', 1)
        
        if position_size > self.max_position_per_trade:
            risk_result['warnings'].append(
                f"仓位大小 ${position_size:.2f} 超过单笔最大限制 ${self.max_position_per_trade:.2f}"
            )
            # 调整仓位大小
            risk_result['adjustments']['position_size_usd'] = self.max_position_per_trade
            risk_result['adjustments']['original_position_size_usd'] = position_size
        
        # 2. 审核杠杆倍数
        if leverage > self.max_leverage:
            risk_result['warnings'].append(
                f"杠杆倍数 {leverage}x 超过最大限制 {self.max_leverage}x"
            )
            risk_result['adjustments']['leverage'] = self.max_leverage
            risk_result['adjustments']['original_leverage'] = leverage
        
        # 3. 计算潜在回撤风险
        stop_loss_pct = decision.get('stop_loss_pct', 0)
        if stop_loss_pct:
            # 计算最大损失金额（考虑杠杆）
            adjusted_leverage = risk_result['adjustments'].get('leverage', leverage)
            max_loss = position_size * (abs(stop_loss_pct) / 100) * adjusted_leverage
            risk_result['risk_metrics']['max_loss_usd'] = max_loss
            
            # 获取账户余额
            try:
                balance = await asyncio.to_thread(self.trader.get_balance)
                if balance:
                    drawdown_pct = (max_loss / balance) * 100
                    risk_result['risk_metrics']['drawdown_pct'] = drawdown_pct
                    
                    if drawdown_pct > self.max_drawdown_pct:
                        risk_result['warnings'].append(
                            f"潜在回撤 {drawdown_pct:.2f}% 超过最大限制 {self.max_drawdown_pct}%"
                        )
                        # 降低仓位以控制回撤
                        safe_position_size = (balance * self.max_drawdown_pct / 100) / (
                            abs(stop_loss_pct) / 100 * adjusted_leverage
                        )
                        risk_result['adjustments']['position_size_usd'] = min(
                            safe_position_size,
                            risk_result['adjustments'].get('position_size_usd', position_size)
                        )
            except Exception as e:
                logger.warning(f"⚠️ 获取账户余额失败: {e}")
        
        # 4. 计算风险收益比
        take_profit_pct = decision.get('take_profit_pct', 0)
        if stop_loss_pct and take_profit_pct:
            risk_reward_ratio = abs(take_profit_pct) / abs(stop_loss_pct)
            risk_result['risk_metrics']['risk_reward_ratio'] = risk_reward_ratio
            
            if risk_reward_ratio < 1.5:
                risk_result['warnings'].append(
                    f"风险收益比 {risk_reward_ratio:.2f} 低于建议值 1.5"
                )
        
        # 5. 评估信心度
        confidence = decision.get('confidence', 50)
        if confidence < 60:
            risk_result['warnings'].append(
                f"信心度 {confidence}% 偏低，建议谨慎操作"
            )
        
        # 根据警告数量判断是否批准
        if len(risk_result['warnings']) >= 3:
            risk_result['approved'] = False
            risk_result['rejection_reason'] = "风险指标超标过多，拒绝执行"
        
        # 计算综合风险等级
        risk_level = self._calculate_risk_level(risk_result)
        risk_result['risk_metrics']['risk_level'] = risk_level
        
        return risk_result
    
    async def analyze_portfolio_risk(
        self,
        decisions: List[Dict[str, Any]],
        current_positions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        分析投资组合的整体风险
        
        Args:
            decisions: 待执行的决策列表
            current_positions: 当前持仓列表
            
        Returns:
            组合风险分析结果
        """
        portfolio_risk = {
            'approved': True,
            'warnings': [],
            'metrics': {},
            'position_count': 0,
            'total_exposure': 0,
            'total_risk': 0
        }
        
        try:
            # 获取当前持仓
            if current_positions is None:
                current_positions = await asyncio.to_thread(self.trader.fetch_positions)
            
            # 统计当前持仓
            active_positions = [p for p in current_positions if p.get('contracts', 0) != 0]
            portfolio_risk['position_count'] = len(active_positions)
            
            # 计算当前总敞口
            current_exposure = sum(
                abs(p.get('contracts', 0) * p.get('contractSize', 1) * p.get('markPrice', 0))
                for p in active_positions
            )
            
            # 计算新增敞口
            new_exposure = sum(
                decision.get('position_size_usd', 0) * decision.get('leverage', 1)
                for decision in decisions
                if decision.get('action') in TradingAction.OPEN_ACTIONS
            )
            
            total_exposure = current_exposure + new_exposure
            portfolio_risk['total_exposure'] = total_exposure
            portfolio_risk['current_exposure'] = current_exposure
            portfolio_risk['new_exposure'] = new_exposure
            
            # 1. 检查总敞口
            if total_exposure > self.max_total_exposure:
                portfolio_risk['warnings'].append(
                    f"总敞口 ${total_exposure:.2f} 超过限制 ${self.max_total_exposure:.2f}"
                )
                portfolio_risk['approved'] = False
            
            # 2. 检查持仓数量
            new_positions = sum(
                1 for decision in decisions
                if decision.get('action') in TradingAction.OPEN_ACTIONS
            )
            total_positions = portfolio_risk['position_count'] + new_positions
            
            if total_positions > self.max_positions:
                portfolio_risk['warnings'].append(
                    f"持仓数量 {total_positions} 超过限制 {self.max_positions}"
                )
                portfolio_risk['approved'] = False
            
            # 3. 计算相关性风险（简化版：检查多个币种的方向）
            # 统计做多和做空的数量
            long_count = sum(
                1 for decision in decisions
                if decision.get('action') == TradingAction.OPEN_LONG
            )
            short_count = sum(
                1 for decision in decisions
                if decision.get('action') == TradingAction.OPEN_SHORT
            )
            
            portfolio_risk['metrics']['long_count'] = long_count
            portfolio_risk['metrics']['short_count'] = short_count
            
            # 如果全部同向，风险较高
            if long_count > 0 and short_count == 0:
                portfolio_risk['warnings'].append(
                    "所有新仓位均为做多，缺乏对冲"
                )
                portfolio_risk['metrics']['diversification'] = 'low'
            elif short_count > 0 and long_count == 0:
                portfolio_risk['warnings'].append(
                    "所有新仓位均为做空，缺乏对冲"
                )
                portfolio_risk['metrics']['diversification'] = 'low'
            else:
                portfolio_risk['metrics']['diversification'] = 'medium'
            
            # 4. 计算总风险额度
            total_risk = sum(
                decision.get('risk_usd', 0)
                for decision in decisions
                if decision.get('action') in TradingAction.OPEN_ACTIONS
            )
            portfolio_risk['total_risk'] = total_risk
            
            # 获取账户余额计算风险比例
            balance = await asyncio.to_thread(self.trader.get_balance)
            if balance:
                risk_pct = (total_risk / balance) * 100
                portfolio_risk['metrics']['total_risk_pct'] = risk_pct
                
                if risk_pct > self.max_drawdown_pct:
                    portfolio_risk['warnings'].append(
                        f"总风险 {risk_pct:.2f}% 超过最大回撤限制 {self.max_drawdown_pct}%"
                    )
            
            # 计算整体风险等级
            portfolio_risk['metrics']['risk_level'] = self._calculate_portfolio_risk_level(
                portfolio_risk
            )
            
        except Exception as e:
            logger.exception(f"❌ 组合风险分析失败: {e}")
            portfolio_risk['warnings'].append(f"分析失败: {str(e)}")
        
        return portfolio_risk
    
    def _calculate_risk_level(self, risk_result: Dict[str, Any]) -> str:
        """计算单个决策的风险等级"""
        warnings_count = len(risk_result['warnings'])
        
        if not risk_result['approved']:
            return RiskLevel.CRITICAL
        elif warnings_count >= 2:
            return RiskLevel.HIGH
        elif warnings_count == 1:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _calculate_portfolio_risk_level(self, portfolio_risk: Dict[str, Any]) -> str:
        """计算组合的整体风险等级"""
        warnings_count = len(portfolio_risk['warnings'])
        
        if not portfolio_risk['approved']:
            return RiskLevel.CRITICAL
        elif warnings_count >= 3:
            return RiskLevel.HIGH
        elif warnings_count >= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW


async def risk_analysis_node(state: TradingState) -> TradingState:
    """
    风险分析节点
    
    功能：
    1. 审核每个决策的仓位大小是否合理
    2. 计算潜在回撤风险
    3. 评估多币种组合风险
    4. 对超出风险限制的决策进行调整或拒绝
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    logger.info("=" * 80)
    logger.info("🛡️ RiskAnalysisAgent: 开始风险分析")
    logger.info("=" * 80)
    
    try:
        decisions = state.get("ai_decisions", [])
        
        if not decisions:
            logger.info("⚠️ 没有需要分析的决策")
            state["risk_analysis"] = {
                "analyzed": False,
                "reason": "no_decisions"
            }
            return state
        
        # 创建风险分析器
        analyzer = RiskAnalyzer(
            session_id=state["session_id"],
            risk_params=state["risk_params"]
        )
        
        # 1. 分析每个决策的风险
        logger.info(f"📊 分析 {len(decisions)} 个决策的风险...")
        decision_risks = []
        
        for i, decision in enumerate(decisions, 1):
            logger.info(f"  分析决策 [{i}/{len(decisions)}]: {decision['symbol']} {decision['action']}")
            risk_result = await analyzer.analyze_decision(decision)
            decision_risks.append(risk_result)
            
            # 打印风险分析结果
            if risk_result['warnings']:
                logger.warning(f"  ⚠️ 发现 {len(risk_result['warnings'])} 个风险警告:")
                for warning in risk_result['warnings']:
                    logger.warning(f"    - {warning}")
            
            if risk_result['adjustments']:
                logger.info(f"  🔧 应用风险调整:")
                for key, value in risk_result['adjustments'].items():
                    if not key.startswith('original_'):
                        logger.info(f"    - {key}: {value}")
            
            logger.info(f"  风险等级: {risk_result['risk_metrics'].get('risk_level', 'unknown')}")
            logger.info(f"  是否批准: {'✅ 是' if risk_result['approved'] else '❌ 否'}")
        
        # 2. 分析组合风险
        logger.info("📊 分析投资组合风险...")
        portfolio_risk = await analyzer.analyze_portfolio_risk(decisions)
        
        logger.info(f"  当前持仓数: {portfolio_risk['position_count']}")
        logger.info(f"  当前敞口: ${portfolio_risk.get('current_exposure', 0):.2f}")
        logger.info(f"  新增敞口: ${portfolio_risk.get('new_exposure', 0):.2f}")
        logger.info(f"  总敞口: ${portfolio_risk['total_exposure']:.2f}")
        logger.info(f"  组合风险等级: {portfolio_risk['metrics'].get('risk_level', 'unknown')}")
        
        if portfolio_risk['warnings']:
            logger.warning(f"  ⚠️ 发现 {len(portfolio_risk['warnings'])} 个组合风险警告:")
            for warning in portfolio_risk['warnings']:
                logger.warning(f"    - {warning}")
        
        # 3. 应用风险调整和过滤
        approved_decisions = []
        rejected_decisions = []
        
        for decision, risk_result in zip(decisions, decision_risks):
            # 应用调整
            if risk_result['adjustments']:
                for key, value in risk_result['adjustments'].items():
                    if not key.startswith('original_'):
                        decision[key] = value
            
            # 附加风险信息
            decision['risk_analysis'] = {
                'approved': risk_result['approved'],
                'warnings': risk_result['warnings'],
                'risk_level': risk_result['risk_metrics'].get('risk_level', 'unknown'),
                'risk_metrics': risk_result['risk_metrics']
            }
            
            # 根据批准状态分类
            if risk_result['approved'] and portfolio_risk['approved']:
                approved_decisions.append(decision)
            else:
                rejected_decisions.append(decision)
                if not risk_result['approved']:
                    logger.warning(
                        f"  ❌ 拒绝决策: {decision['symbol']} {decision['action']} - "
                        f"{risk_result.get('rejection_reason', '风险过高')}"
                    )
        
        # 如果组合风险不通过，拒绝所有开仓决策
        if not portfolio_risk['approved']:
            logger.warning("  ❌ 组合风险不通过，拒绝所有新开仓决策")
            approved_decisions = [
                d for d in approved_decisions
                if d['action'] not in TradingAction.OPEN_ACTIONS
            ]
            rejected_decisions.extend([
                d for d in decisions
                if d['action'] in TradingAction.OPEN_ACTIONS and d not in rejected_decisions
            ])
        
        logger.info("=" * 80)
        logger.info(f"✅ 风险分析完成:")
        logger.info(f"  批准: {len(approved_decisions)} 个")
        logger.info(f"  拒绝: {len(rejected_decisions)} 个")
        logger.info("=" * 80)
        
        # 4. 更新状态
        state["ai_decisions"] = approved_decisions
        state["risk_analysis"] = {
            "analyzed": True,
            "decision_risks": decision_risks,
            "portfolio_risk": portfolio_risk,
            "approved_count": len(approved_decisions),
            "rejected_count": len(rejected_decisions),
            "rejected_decisions": rejected_decisions
        }
        
        # 更新调试信息
        if "debug_info" not in state:
            state["debug_info"] = {}
        state["debug_info"]["risk_analysis_completed_at"] = datetime.now().isoformat()
        state["debug_info"]["risk_approved_count"] = len(approved_decisions)
        state["debug_info"]["risk_rejected_count"] = len(rejected_decisions)
        
        return state
        
    except Exception as e:
        logger.exception(f"❌ RiskAnalysisAgent 执行失败: {e}")
        
        # 记录错误
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(f"RiskAnalysisAgent: {str(e)}")
        
        # 出错时保持原决策不变，但标记分析失败
        state["risk_analysis"] = {
            "analyzed": False,
            "error": str(e)
        }
        
        # 不抛出异常，继续执行流程
        return state

