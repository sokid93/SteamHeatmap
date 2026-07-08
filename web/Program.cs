using SteamHeatmap.Web.Domain;
using SteamHeatmap.Web.Infrastructure;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllersWithViews();

var connectionString = builder.Configuration["SUPABASE_DB_URL"]
    ?? throw new InvalidOperationException("SUPABASE_DB_URL is not configured.");
builder.Services.AddSingleton<IRankingRepository>(new PostgresRankingRepository(connectionString));
builder.Services.AddScoped<RegionMapViewModelBuilder>();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error");
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();

app.UseRouting();

app.UseAuthorization();

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}");

app.Run();
