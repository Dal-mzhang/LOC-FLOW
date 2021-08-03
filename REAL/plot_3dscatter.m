%plot location distribution in 3d
loc = './catalogSA_allday.txt'

a = load(loc);
lat = a(:,7);
lon = a(:,8);
dep = a(:,9);

scatter3(lon,lat,dep,'filled','b'), view(-60,60);
ylim([42.5,43.0]) %lat range
xlim([12.9,13.4]) %lon range
zlim([0,20]);   %dep range
grid on; alpha(0.45); box on;
set(gca,'zDir','reverse');
xlabel('Lon.');
ylabel('Lat.');
zlabel('Depth');
set(gca,'FontSize',20)
%saveas(gcf,'3Dlocation.pdf')
