%plot location distribution in 3d
clc;clear all;close all;

%initial locations (please choose one,
% and be consistent with your previous steps)
%REAL's simulated annealing locations (hypo=0)
%loc1 = '../REAL/catalogSA_allday.txt'
%a = load(loc1); lat1 = a(:,7); lon1 = a(:,8); dep1 = a(:,9);
%title1 = 'REAL catalog (SA)'

%VELEST's locations (hypo=1)
%loc1 = '../location/VELEST/new.cat' 
%a = load(loc1); lat1 = a(:,5); lon1 = a(:,6); dep1 = a(:,7);
%title1 = 'VELEST catalog'

%hypoinverse's locations (hypo=2)
loc1 = '../location/hypoinverse/new.cat'
a = load(loc1); lat1 = a(:,5); lon1 = a(:,6); dep1 = a(:,7);
title1 = 'HYPOINVERSE catalog'

%hypoinverse_corr's locations (hypo=3)
%loc1 = '../location/hypoinverse_corr/new.cat'
%a = load(loc1); lat1 = a(:,5); lon1 = a(:,6); dep1 = a(:,7);
%title1 = 'HYPOINVERSE\_corr catalog'

% you may only show those events with P's DT or CC constraints
% also consider useall=0 in hypoDD_dtcc/run_hypoDD_dtcc.sh and GrowClust/IN/gen_input.pl
nddp = 0;
%nddp = 5;
%hypoDD dt.ct locations
loc2 = '../hypoDD_dtct/hypoDD.reloc'
b = load(loc2);
id=find(b(:,20) >= nddp);
lat2 = b(id,2); lon2 = b(id,3); dep2 = b(id,4);

%hypoDD dt.cc locations
loc3 = '../hypoDD_dtcc/hypoDD.reloc'
c = load(loc3); 
id=find(c(:,18) >= nddp);
lat3 = c(id,2); lon3 = c(id,3); dep3 = c(id,4);

%GrowClust cc locations
%loc4 = '../MatchLocate/GrowClust/OUT/out.growclust_cat'
loc4 = '../GrowClust/OUT/out.growclust_cat'
d = load(loc4); npar = 0;
id=find(d(:,15) >= npar & d(:,16) >= nddp);
lat4 = d(id,8); lon4 = d(id,9); dep4 = d(id,10);

minlat=min([min(lat1), min(lat2), min(lat3), min(lat4)]);
maxlat=max([max(lat1), max(lat2), max(lat3), max(lat4)]);

minlon=min([min(lon1), min(lon2), min(lon3), min(lon4)]);
maxlon=max([max(lon1), max(lon2), max(lon3), max(lon4)]);

mindep=min([min(dep1), min(dep2), min(dep3), min(dep4)]);
maxdep=max([max(dep1), max(dep2), max(dep3), max(dep4)]);

xmin=minlon; xmax=maxlon;
ymin=minlat; ymax=maxlat;
zmin=0; zmax=maxdep;
dx=0.2; dy=0.2; dz=5;

%2D map view (lon. vs. lat.)
view1=0;
view2=90;

%3D view
% view1=23;
% view2=15;

%2D depth view (lon. vs dep)
%view1=0;
%view2=0;

%manually specify the region
%the whole region
xmin=12.9; xmax=13.4;
ymin=42.45; ymax=43.0;
zmin=0; zmax=18;
dx=0.2; dy=0.2; dz=5;

%the zoomed region (one-day data)
%xmin=13.31; xmax=13.338;
%ymin=42.635; ymax=42.655;
%zmin=7.8; zmax=11;
%dx=0.004; dy=0.003; dz=0.5;

%only show events within the region
id =  find(lon1(:,1) >= xmin & lon1(:,1) <= xmax & lat1(:,1) >= ymin & lat1(:,1) <= ymax & dep1(:,1) >= zmin & dep1(:,1) <= zmax);
lon1 = lon1(id,1);
lat1 = lat1(id,1);
dep1 = dep1(id,1);

id =  find(lon2(:,1) >= xmin & lon2(:,1) <= xmax & lat2(:,1) >= ymin & lat2(:,1) <= ymax & dep2(:,1) >= zmin & dep2(:,1) <= zmax);
lon2 = lon2(id,1);
lat2 = lat2(id,1);
dep2 = dep2(id,1);

id =  find(lon3(:,1) >= xmin & lon3(:,1) <= xmax & lat3(:,1) >= ymin & lat3(:,1) <= ymax & dep3(:,1) >= zmin & dep3(:,1) <= zmax);
lon3 = lon3(id,1);
lat3 = lat3(id,1);
dep3 = dep3(id,1);

id =  find(lon4(:,1) >= xmin & lon4(:,1) <= xmax & lat4(:,1) >= ymin & lat4(:,1) <= ymax & dep4(:,1) >= zmin & dep4(:,1) <= zmax);
lon4 = lon4(id,1);
lat4 = lat4(id,1);
dep4 = dep4(id,1);


%accurately adjust the figure position
% fig_width=0.35; fig_height=0.35;
% fromY_221=0.1; fromX_221=0.55;
% fromY_222=0.5; fromX_222=0.55;
% fromY_223=0.1; fromX_223=0.1;
% fromY_224=0.5; fromX_224=0.1;

%plot initial locations
set(gcf,'position',[50 50 1200 400])
subplot(2,2,1) % use below option if you want to adjust the figure
%positionVector = [fromY_221,  fromX_221, fig_width,fig_height];
%subplot('Position',positionVector)
scatter3(lon1,lat1,dep1,'filled','b','LineWidth',0.03), view(view1,view2);
xlim([xmin,xmax])  %lon range  
ylim([ymin,ymax])  %lat range
zlim([zmin,zmax]);  %dep range
grid on; alpha(0.45); box on;
set(gca,'zDir','reverse');
xlabel('Lon.');
ylabel('Lat.');
zlabel('Depth');
set(gca,'FontSize',10)
set(gca,'XTick',xmin:dx:xmax);
set(gca,'YTick',ymin:dy:ymax); 
set(gca,'ZTick',zmin:dz:zmax);
hold on;
title(title1,length(lat1));

%plot the hypoDD dtct locations
subplot(2,2,2) % use below option if you want to adjust the figure
%positionVector = [fromY_222,  fromX_222, fig_width,fig_height];
%subplot('Position',positionVector)
scatter3(lon2,lat2,dep2,'filled','b','LineWidth',0.03), view(view1,view2);
xlim([xmin,xmax])  %lon range  
ylim([ymin,ymax])  %lat range
zlim([zmin,zmax]);  %dep range
grid on; alpha(0.45); box on;
set(gca,'zDir','reverse');
xlabel('Lon.');
ylabel('Lat.');
zlabel('Depth');
set(gca,'FontSize',10)
set(gca,'XTick',xmin:dx:xmax);
set(gca,'YTick',ymin:dy:ymax); 
set(gca,'ZTick',zmin:dz:zmax);
title('hypoDD catalog (dt.ct)',length(lat2));

%plot the hypoDD dtcc locations
subplot(2,2,3) % use below option if you want to adjust the figure
%positionVector = [fromY_223,  fromX_223, fig_width,fig_height];
%subplot('Position',positionVector)
scatter3(lon3,lat3,dep3,'filled','b','LineWidth',0.03), view(view1,view2);
xlim([xmin,xmax])  %lon range  
ylim([ymin,ymax])  %lat range
zlim([zmin,zmax]);  %dep range
grid on; alpha(0.45); box on;
set(gca,'zDir','reverse');
xlabel('Lon.');
ylabel('Lat.');
zlabel('Depth');
set(gca,'FontSize',10)
set(gca,'XTick',xmin:dx:xmax);
set(gca,'YTick',ymin:dy:ymax); 
set(gca,'ZTick',zmin:dz:zmax);
title('hypoDD catalog (dt.cc)',length(lat3));

%plot the GrowClust locations
subplot(2,2,4) % % use below option if you want to adjust the figure
%positionVector = [fromY_224,  fromX_224, fig_width,fig_height];
%subplot('Position',positionVector)
scatter3(lon4,lat4,dep4,'filled','b','LineWidth',0.03), view(view1,view2);
xlim([xmin,xmax])  %lon range  
ylim([ymin,ymax])  %lat range
zlim([zmin,zmax]);  %dep range
grid on; alpha(0.45); box on;
set(gca,'zDir','reverse');
xlabel('Lon.');
ylabel('Lat.');
zlabel('Depth');
set(gca,'FontSize',10)
set(gca,'XTick',xmin:dx:xmax);
set(gca,'YTick',ymin:dy:ymax); 
set(gca,'ZTick',zmin:dz:zmax);
title('GrowClust catalog',length(lat4));
%title('Template Matching + GrowClust catalog',length(lat4));
saveas(gcf,'3Dlocation.jpg')
%saveas(gcf,'3Dlocation.pdf')
