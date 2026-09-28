/**
 * StateStore - 全局状态管理
 * 采用单例模式，通过 dispatch 方法传递状态
 * 用于污点泄露 benchmark：deviceinfo.brand → dispatch → hilog.info
 */
export class StoreState {
    brand: string = '';
    dispatchedAction: string = '';
}
export class StateStore {
    private static instance: StateStore | null = null;
    private state: StoreState;
    private constructor() {
        this.state = new StoreState();
    }
    static getInstance(): StateStore {
        if (StateStore.instance === null) {
            StateStore.instance = new StateStore();
        }
        return StateStore.instance;
    }
    dispatch(action: string, payload: string): void {
        this.state.dispatchedAction = action;
        if (action === 'SET_BRAND') {
            this.state.brand = payload;
        }
    }
    getState(): StoreState {
        return this.state;
    }
}
