.class public Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;
.super Lcom/android/launcher3/ExtendedEditText;
.source "SourceFile"

# interfaces
.implements Lcom/android/launcher3/allapps/search/AllAppsSearchBarController$Callbacks;


# instance fields
.field private bT:Lcom/google/android/apps/nexuslauncher/qsb/AllAppsQsbLayout;

.field private mAdapter:Lcom/android/launcher3/allapps/AllAppsGridAdapter;

.field private mApps:Lcom/android/launcher3/allapps/AlphabeticalAppsList;

.field private mAppsRecyclerView:Lcom/android/launcher3/allapps/AllAppsRecyclerView;

.field private final mSearchBarController:Lcom/android/launcher3/allapps/search/AllAppsSearchBarController;


# direct methods
.method public constructor <init>(Landroid/content/Context;)V
    .locals 1

    .prologue
    .line 34
    const/4 v0, 0x0

    invoke-direct {p0, p1, v0}, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;)V

    .line 35
    return-void
.end method

.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;)V
    .locals 1

    .prologue
    .line 38
    const/4 v0, 0x0

    invoke-direct {p0, p1, p2, v0}, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;I)V

    .line 39
    return-void
.end method

.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;I)V
    .locals 1

    .prologue
    .line 42
    invoke-direct {p0, p1, p2, p3}, Lcom/android/launcher3/ExtendedEditText;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;I)V

    .line 43
    new-instance v0, Lcom/android/launcher3/allapps/search/AllAppsSearchBarController;

    invoke-direct {v0}, Lcom/android/launcher3/allapps/search/AllAppsSearchBarController;-><init>()V

    iput-object v0, p0, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->mSearchBarController:Lcom/android/launcher3/allapps/search/AllAppsSearchBarController;

    .line 44
    return-void
.end method

.method private notifyResultChanged()V
    .locals 2

    .prologue
    .line 79
    iget-object v0, p0, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->bT:Lcom/google/android/apps/nexuslauncher/qsb/AllAppsQsbLayout;

    const/4 v1, 0x0

    invoke-virtual {v0, v1}, Lcom/google/android/apps/nexuslauncher/qsb/AllAppsQsbLayout;->bv(I)V

    .line 80
    iget-object v0, p0, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->mAppsRecyclerView:Lcom/android/launcher3/allapps/AllAppsRecyclerView;

    invoke-virtual {v0}, Lcom/android/launcher3/allapps/AllAppsRecyclerView;->onSearchResultsChanged()V

    .line 81
    return-void
.end method


# virtual methods
.method public bu(Lcom/google/android/apps/nexuslauncher/qsb/AllAppsQsbLayout;Lcom/android/launcher3/allapps/AlphabeticalAppsList;Lcom/android/launcher3/allapps/AllAppsRecyclerView;)V
    .locals 3

    .prologue
    .line 48
    iput-object p1, p0, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->bT:Lcom/google/android/apps/nexuslauncher/qsb/AllAppsQsbLayout;

    .line 49
    iput-object p2, p0, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->mApps:Lcom/android/launcher3/allapps/AlphabeticalAppsList;

    .line 50
    iput-object p3, p0, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->mAppsRecyclerView:Lcom/android/launcher3/allapps/AllAppsRecyclerView;

    .line 51
    iget-object v0, p0, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->mAppsRecyclerView:Lcom/android/launcher3/allapps/AllAppsRecyclerView;

    invoke-virtual {v0}, Lcom/android/launcher3/allapps/AllAppsRecyclerView;->getAdapter()Landroid/support/v7/widget/q;

    move-result-object v0

    check-cast v0, Lcom/android/launcher3/allapps/AllAppsGridAdapter;

    iput-object v0, p0, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->mAdapter:Lcom/android/launcher3/allapps/AllAppsGridAdapter;

    .line 52
    iget-object v0, p0, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->mSearchBarController:Lcom/android/launcher3/allapps/search/AllAppsSearchBarController;

    new-instance v1, Lcom/google/android/apps/nexuslauncher/search/b;

    invoke-virtual {p0}, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->getContext()Landroid/content/Context;

    move-result-object v2

    invoke-direct {v1, v2}, Lcom/google/android/apps/nexuslauncher/search/b;-><init>(Landroid/content/Context;)V

    .line 53
    invoke-virtual {p0}, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->getContext()Landroid/content/Context;

    move-result-object v2

    invoke-static {v2}, Lcom/android/launcher3/Launcher;->getLauncher(Landroid/content/Context;)Lcom/android/launcher3/Launcher;

    move-result-object v2

    .line 52
    invoke-virtual {v0, v1, p0, v2, p0}, Lcom/android/launcher3/allapps/search/AllAppsSearchBarController;->initialize(Lcom/android/launcher3/allapps/search/SearchAlgorithm;Lcom/android/launcher3/ExtendedEditText;Lcom/android/launcher3/Launcher;Lcom/android/launcher3/allapps/search/AllAppsSearchBarController$Callbacks;)V

    .line 54
    return-void
.end method

.method public clearSearchResult()V
    .locals 2

    .prologue
    const/4 v1, 0x0

    .line 67
    invoke-virtual {p0}, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->getParent()Landroid/view/ViewParent;

    move-result-object v0

    if-eqz v0, :cond_0

    .line 68
    iget-object v0, p0, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->mApps:Lcom/android/launcher3/allapps/AlphabeticalAppsList;

    invoke-virtual {v0, v1}, Lcom/android/launcher3/allapps/AlphabeticalAppsList;->setOrderedFilter(Ljava/util/ArrayList;)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 69
    invoke-direct {p0}, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->notifyResultChanged()V

    .line 72
    :cond_0
    return-void
.end method

.method public onSearchResult(Ljava/lang/String;Ljava/util/ArrayList;)V
    .locals 1

    .prologue
    .line 58
    if-eqz p2, :cond_0

    invoke-virtual {p0}, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->getParent()Landroid/view/ViewParent;

    move-result-object v0

    if-eqz v0, :cond_0

    .line 59
    iget-object v0, p0, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->mApps:Lcom/android/launcher3/allapps/AlphabeticalAppsList;

    invoke-virtual {v0, p2}, Lcom/android/launcher3/allapps/AlphabeticalAppsList;->setOrderedFilter(Ljava/util/ArrayList;)Z

    .line 60
    invoke-direct {p0}, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->notifyResultChanged()V

    .line 61
    iget-object v0, p0, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->mAdapter:Lcom/android/launcher3/allapps/AllAppsGridAdapter;

    invoke-virtual {v0, p1}, Lcom/android/launcher3/allapps/AllAppsGridAdapter;->setLastSearchQuery(Ljava/lang/String;)V

    .line 63
    :cond_0
    return-void
.end method

.method public refreshSearchResult()V
    .locals 1

    .prologue
    .line 75
    iget-object v0, p0, Lcom/google/android/apps/nexuslauncher/qsb/FallbackAppsSearchView;->mSearchBarController:Lcom/android/launcher3/allapps/search/AllAppsSearchBarController;

    invoke-virtual {v0}, Lcom/android/launcher3/allapps/search/AllAppsSearchBarController;->refreshSearchResult()V

    .line 76
    return-void
.end method
