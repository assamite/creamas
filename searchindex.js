Search.setIndex({envversion:50,filenames:["agent","agents","api","artifact","core","create_agent","create_sim","ds","environment","feature","features","index","install","logging","mapper","mappers","math","mp","overview","rule","simulation"],objects:{"":{agent:[0,0,0,"-"],agents:[1,0,0,"-"],ds:[7,0,0,"-"],environment:[8,0,0,"-"],feature:[9,0,0,"-"],features:[10,0,0,"-"],logging:[13,0,0,"-"],mapper:[14,0,0,"-"],mappers:[15,0,0,"-"],math:[16,0,0,"-"],mp:[17,0,0,"-"],rule:[19,0,0,"-"],simulation:[20,0,0,"-"]},"creamas.agents":{NumberAgent:[1,1,1,""]},"creamas.agents.NumberAgent":{invent_number:[1,2,1,""]},"creamas.core":{agent:[0,0,0,"-"],artifact:[3,0,0,"-"],environment:[8,0,0,"-"],feature:[9,0,0,"-"],mapper:[14,0,0,"-"],rule:[19,0,0,"-"],simulation:[20,0,0,"-"]},"creamas.core.agent":{CreativeAgent:[0,1,1,""]},"creamas.core.agent.CreativeAgent":{A:[0,3,1,""],D:[0,3,1,""],R:[0,3,1,""],W:[0,3,1,""],act:[0,2,1,""],add_artifact:[0,2,1,""],add_connection:[0,2,1,""],add_rule:[0,2,1,""],age:[0,3,1,""],ask_opinion:[0,2,1,""],attitudes:[0,3,1,""],close:[0,2,1,""],connect:[0,2,1,""],connections:[0,3,1,""],cur_res:[0,3,1,""],env:[0,3,1,""],evaluate:[0,2,1,""],get_attitude:[0,2,1,""],get_older:[0,2,1,""],get_weight:[0,2,1,""],max_res:[0,3,1,""],name:[0,3,1,""],publish:[0,2,1,""],qualname:[0,2,1,""],random_connection:[0,2,1,""],refill:[0,2,1,""],remove_connection:[0,2,1,""],remove_rule:[0,2,1,""],sanitized_name:[0,2,1,""],set_attitude:[0,2,1,""],set_weight:[0,2,1,""],validate:[0,2,1,""],vote:[0,2,1,""]},"creamas.core.artifact":{Artifact:[3,1,1,""]},"creamas.core.artifact.Artifact":{add_eval:[3,2,1,""],creator:[3,3,1,""],domain:[3,2,1,""],evals:[3,3,1,""],framings:[3,3,1,""],obj:[3,3,1,""]},"creamas.core.environment":{Environment:[8,1,1,""]},"creamas.core.environment.Environment":{add_artifact:[8,2,1,""],add_artifacts:[8,2,1,""],add_candidate:[8,2,1,""],age:[8,3,1,""],artifacts:[8,3,1,""],candidates:[8,3,1,""],clear_candidates:[8,2,1,""],create_initial_connections:[8,2,1,""],destroy:[8,2,1,""],get_agents:[8,2,1,""],get_artifacts:[8,2,1,""],get_random_agent:[8,2,1,""],is_ready:[8,2,1,""],log_folder:[8,3,1,""],logger:[8,3,1,""],name:[8,3,1,""],perform_voting:[8,2,1,""],save_info:[8,2,1,""],trigger_act:[8,2,1,""],trigger_all:[8,2,1,""],validate_candidates:[8,2,1,""]},"creamas.core.feature":{Feature:[9,1,1,""]},"creamas.core.feature.Feature":{domains:[9,3,1,""],extract:[9,2,1,""],name:[9,3,1,""],rtype:[9,3,1,""]},"creamas.core.mapper":{Mapper:[14,1,1,""]},"creamas.core.mapper.Mapper":{map:[14,2,1,""]},"creamas.core.rule":{Rule:[19,1,1,""]},"creamas.core.rule.Rule":{R:[19,3,1,""],W:[19,3,1,""],add_subrule:[19,2,1,""],domains:[19,3,1,""]},"creamas.core.simulation":{Simulation:[20,1,1,""]},"creamas.core.simulation.Simulation":{age:[20,3,1,""],async_step:[20,2,1,""],callback:[20,3,1,""],create:[20,4,1,""],end:[20,2,1,""],env:[20,3,1,""],finish_step:[20,2,1,""],name:[20,3,1,""],next:[20,2,1,""],order:[20,3,1,""],step:[20,2,1,""],steps:[20,2,1,""]},"creamas.ds":{DistributedEnvironment:[7,1,1,""],ssh_exec:[7,5,1,""],ssh_exec_in_new_loop:[7,5,1,""]},"creamas.ds.DistributedEnvironment":{destroy:[7,2,1,""],env:[7,3,1,""],manager_addrs:[7,3,1,""],nodes:[7,3,1,""],prepare_nodes:[7,2,1,""],spawn_nodes:[7,2,1,""],stop_nodes:[7,2,1,""],trigger_all:[7,2,1,""],wait_nodes:[7,2,1,""]},"creamas.features":{ModuloFeature:[10,1,1,""]},"creamas.features.ModuloFeature":{n:[10,3,1,""]},"creamas.logging":{ObjectLogger:[13,1,1,""],log_after:[13,5,1,""],log_before:[13,5,1,""]},"creamas.logging.ObjectLogger":{add_handler:[13,2,1,""],folder:[13,3,1,""],get_file:[13,2,1,""],log_attr:[13,2,1,""],obj:[13,3,1,""],write:[13,2,1,""]},"creamas.mappers":{BooleanMapper:[15,1,1,""],DoubleLinearMapper:[15,1,1,""],GaussianMapper:[15,1,1,""],LinearMapper:[15,1,1,""],LogisticMapper:[15,1,1,""]},"creamas.mappers.BooleanMapper":{mode:[15,3,1,""]},"creamas.mappers.DoubleLinearMapper":{mode:[15,3,1,""],value_set:[15,3,1,""]},"creamas.mappers.GaussianMapper":{mode:[15,3,1,""]},"creamas.mappers.LinearMapper":{mode:[15,3,1,""],value_set:[15,3,1,""]},"creamas.mappers.LogisticMapper":{mode:[15,3,1,""]},"creamas.math":{gaus_pdf:[16,5,1,""],logistic:[16,5,1,""]},"creamas.mp":{EnvManager:[17,1,1,""],MultiEnvManager:[17,1,1,""],MultiEnvironment:[17,1,1,""],spawn_container:[17,5,1,""],spawn_containers:[17,5,1,""],start:[17,5,1,""]},"creamas.mp.EnvManager":{act:[17,2,1,""],add_candidate:[17,2,1,""],artifacts:[17,2,1,""],candidates:[17,2,1,""],clear_candidates:[17,2,1,""],get_agents:[17,2,1,""],get_artifacts:[17,2,1,""],get_older:[17,2,1,""],handle:[17,2,1,""],host_addr:[17,2,1,""],is_ready:[17,2,1,""],report:[17,2,1,""],set_host_addr:[17,2,1,""],spawn_n:[17,2,1,""],stop:[17,2,1,""],trigger_all:[17,2,1,""],validate:[17,2,1,""],validate_candidates:[17,2,1,""],vote:[17,2,1,""]},"creamas.mp.MultiEnvManager":{act:[17,2,1,""],add_candidate:[17,2,1,""],destroy:[17,2,1,""],get_agents:[17,2,1,""],get_candidates:[17,2,1,""],get_older:[17,2,1,""],get_slave_agents:[17,2,1,""],handle:[17,2,1,""],is_ready:[17,2,1,""],kill:[17,2,1,""],set_host_manager:[17,2,1,""],spawn:[17,2,1,""],spawn_n:[17,2,1,""],trigger_all:[17,2,1,""]},"creamas.mp.MultiEnvironment":{add_artifact:[17,2,1,""],add_artifacts:[17,2,1,""],add_candidate:[17,2,1,""],addrs:[17,3,1,""],age:[17,3,1,""],artifacts:[17,3,1,""],candidates:[17,3,1,""],check_ready:[17,2,1,""],clear_candidates:[17,2,1,""],create_connection:[17,2,1,""],create_initial_connections:[17,2,1,""],destroy:[17,2,1,""],env:[17,3,1,""],get_agents:[17,2,1,""],get_artifacts:[17,2,1,""],get_random_agent:[17,2,1,""],is_ready:[17,2,1,""],manager:[17,3,1,""],name:[17,3,1,""],perform_voting:[17,2,1,""],random_addr:[17,2,1,""],save_info:[17,2,1,""],spawn:[17,2,1,""],trigger_act:[17,2,1,""],trigger_all:[17,2,1,""],validate_candidates:[17,2,1,""]},creamas:{agents:[1,0,0,"-"],ds:[7,0,0,"-"],features:[10,0,0,"-"],logging:[13,0,0,"-"],mappers:[15,0,0,"-"],math:[16,0,0,"-"],mp:[17,0,0,"-"]}},objnames:{"0":["py","module","Python module"],"1":["py","class","Python class"],"2":["py","method","Python method"],"3":["py","attribute","Python attribute"],"4":["py","classmethod","Python class method"],"5":["py","function","Python function"]},objtypes:{"0":"py:module","1":"py:class","2":"py:method","3":"py:attribute","4":"py:classmethod","5":"py:function"},terms:{"boolean":15,"case":17,"class":[],"default":[0,6,7,13,17],"final":20,"float":[0,3,10,14,15,16,19],"function":[],"import":[5,6,9,18,19],"int":[0,3,7,8,10,13,15,17,20],"new":[0,1,7,13,17,18],"return":[0,3,7,8,9,10,13,14,15,16,17,19],"super":5,"true":[0,6,7,8,9,10,13,15,17,19],"while":[14,20],__init__:[5,17],abl:[7,17],about:[0,18],abov:[],absolut:13,accept:[5,8,9,10,15,17,19,20],accumul:[0,8,17,18],act:[0,6,7,8,17,18,20],activ:[12,18],actual:[0,15,17,18],add:[0,3,8,13,17,18,19],add_artifact:[0,8,17],add_candid:[8,17],add_connect:0,add_ev:3,add_handl:13,add_nam:13,add_rul:0,add_subrul:19,added:0,addit:[7,17],addr2:17,addr:[0,8,17,18],address:[0,7,8,17,18],after:[6,7,9,13,14,17,20],afterward:7,age:[0,8,17,20],agent_arg:17,agent_cl:[6,8,17,20],agent_kwarg:[6,17,20],agnost:18,aioma:[0,8,17,18],all:[0,5,6,7,8,9,17,18,19,20],allow:[7,13,18],alphabet:20,alreadi:[0,19,20],also:[1,5,8,17,18,19,20],alter:18,altere:7,alwai:[0,8,17],amount:20,analyz:13,ani:[0,7,8,9,17,18,20],anoth:19,any:17,appli:15,applyasync:17,appreci:14,appropri:9,arg:[0,1,5,6,7,8,17],argument:[6,17,19,20],around:17,artifact:[],as_coro:[8,17],ask:[0,18],ask_opinion:[0,18],assamit:12,associ:[7,8],assum:[7,17],async:[],async_step:20,asynchron:[7,8,17,20],asyncio:7,asyncssh:7,atmospher:6,att:18,attach:19,attitud:[0,18],attr:13,attr_nam:13,attribut:[0,13],automat:6,avail:7,avoid:12,await:[],awar:0,axi:16,back:7,bar:6,base:[0,1,3,4,7,8,9,13,14,15,19,20],base_url:8,basic:[0,1,8,13,17,18,20],becom:18,been:[7,8,17,18],befor:[0,7,8,13],behavior:[7,13],belong:[8,13,14,18],below:0,best:[8,17],between:[7,15,18],bin:12,bodi:19,bookkeep:[0,20],bool:[0,8,17,19],booleanmapp:15,both:8,build:18,built:18,c_req:12,calcul:[6,15],call:[0,5,6,7,8,13,17,19,20],callabl:[0,9,14,17,19,20],callback:20,can:[0,6,7,8,9,12,15,17,18,19,20],candid:[0,8,17],cap:[0,14],cardin:[8,17],carri:13,caught:7,caus:7,cause_havoc:6,certain:[0,8,14,17],chang:[0,3,15,20],check:[7,8,17],check_readi:17,choic:0,classmethod:20,cleanest:[],clear:17,clear_candid:[8,17],clock:[8,17],clone:12,close:[0,7,8,17],cluster:[7,18],cmd:7,code:[5,18],codec:17,coher:8,com:12,combin:[18,19],command:[7,17],common:0,commun:[7,8,17,18],comput:[6,7,18],concaten:15,conflict:12,conn:20,connect:[0,7,8,17,20],connect_kwarg:8,consider:17,consist:[17,19],consum:[8,17],contain:[0,6,7,8,17,18],control:6,conveni:[17,20],core:[],coroutin:17,correctli:8,correspond:[0,18],costli:[8,17],creama:[],creat:[0,1,3,6,7,8,11,12,13,15,17,18,20],create_connect:17,create_initial_connect:[8,17],creation:[0,20],creativ:[],creativeag:[0,1,3,5,6,8,17,18],creator:[3,18],credenti:7,cross:8,crucial:7,cthulhu:6,cthulhu_kwarg:6,cthulhuag:6,cur_r:0,current:[0,6,7,8,17,18,20],curv:[15,16],data:[0,19],decid:[8,17],decis:0,decor:13,dedic:[],def:5,defin:[8,19],densiti:[15,16],depend:[0,7,15,18],deriv:7,design:18,desir:17,destroi:[6,7,8,17,20],detail:[17,18],determin:[8,17],develop:[],deviat:[15,16],dict:[0,3,20],dictionari:0,did:3,diff:18,differ:[6,7,12,15,18],directli:[6,17],directori:0,dislik:18,distribut:[],distributedenviron:7,divid:10,divisor:10,doe:[0,7,8,17,18],domain:[0,3,9,10,18,19],don:18,done:[7,8,19],doublelinearmapp:15,down:[5,6,8,17],drizzl:6,dummi:[0,6,9],dure:[0,7,8,17],each:[0,4,5,6,7,8,9,13,14,17,18,19,20],earli:1,easi:[6,7,18],easiest:12,easili:17,effect:18,effortlessli:18,either:[15,19],encourag:[12,18],end:[6,15,20],ensur:8,env:[0,6,7,17,18,20],env_arg:17,env_cl:[6,17,20],env_kwarg:[6,17,20],env_param:17,enviro:[6,17],enviroment:8,environ:[],envmanag:[7,17],error:7,essential:17,etc:20,eval:3,evalu:[0,1,3,9,15,18,19],evaluat:0,even:7,event:7,exampl:[5,9,18],except:[7,17],exchang:18,exclud:[7,17],execut:[6,7,8,17,18],exist:18,exit:7,expect:[0,16,20],experi:6,expir:7,express:18,extern:7,extra:20,extra_s:17,extract:[9,18],factori:17,fals:[0,8,13,15,17,19],far:0,featur:[],feautr:14,few:[6,17],field:18,file:[0,12,13],finish:17,finish_step:[6,20],first:[5,7,15,17,18,20],focu:18,folder:[0,8,13,17,20],follow:[7,8,15,17],foo:6,form:18,formula:0,four:15,frame:[0,3,8,17],free:7,friendlier:18,from:[0,1,5,6,7,8,9,12,15,17,18,19,20],fulli:[6,8,17,18,20],fundament:18,futur:7,gaus_pdf:16,gaussian:[15,16],gaussianmapp:15,gear:18,gener:13,get:[0,8,17,18],get_ag:[8,17],get_artifact:[8,17],get_attitud:[0,18],get_candid:17,get_event_loop:7,get_fil:13,get_old:[0,17],get_random_ag:[8,17],get_slave_ag:17,get_weight:0,git:12,github:[11,12],give:[18,20],given:[0,1,3,7,8,14,15,17,20],gloomi:6,goal:18,grep:17,grid:17,gridagent:17,guid:18,halt:7,handl:17,handler:13,have:[6,7,9,13,14,15,17,18,20],help:13,high:1,highest:0,hold:[0,1,3,4,6,7,8,9,13,14,17,18,19],homogen:17,host:[7,17],host_addr:17,how:[1,19],howev:[17,18],http:[12,18],human:0,ident:14,identifi:17,implement:[],incl:7,index:11,individu:[7,15,17,18],ineffici:17,inform:[3,8,17,18,20],inher:[8,18],inherit:[1,5,8],inhibit:18,init:13,initi:[0,5,6,7,8,9,14,17,18,20],initial:17,innsmouthenviron:6,input:[9,17],insid:17,instal:[7,12,17],instanc:[13,17,19],instant:[8,17],instanti:20,instead:[7,17],integ:1,intend:[7,17],inter:[7,8],interfac:19,intern:[17,19],interv:[1,9,14,15,18],invent:1,invent_numb:1,irv:[8,17],is_readi:[7,8,17],item:17,iter:[0,4,6,7,18,19,20],iterabl:17,itself:[3,14,17],keep:[],keyboardinterrupt:17,keyword:[6,17,19,20],kill:17,kind:18,know:0,knowledg:[0,18],kwarg:[0,1,5,6,7,8,17],larg:17,larger:[8,17],latest:12,least:[8,17],least_worst:[8,17],left:7,length:[17,19],level:13,lifetim:[0,8,17],like:[7,19],line:15,linear:15,linearli:15,linearmapp:15,list:[0,7,8,9,17,19,20],live:[0,4,5,8],loc:15,localhost:[17,18],log:[],log_aft:13,log_attr:13,log_befor:13,log_fold:[0,8,17,20],log_level:[0,13,17],logger:[6,7,8,13],login:7,logist:[15,16],logisticmapp:15,look:8,loop:7,lot:18,low:1,lyeh:6,machin:[17,18],made:[6,7],mai:[0,17,18],main:[0,6,11,18],mainli:8,make:[0,7,14,17,18],manag:[7,8,17],manager_addr:7,mani:1,manner:[18,20],map:[9,14,15],mapper:[],master:17,match:3,math:[],mathemat:16,max:19,max_r:0,maximum:[0,15,16,19],mean:[0,8,15,16,17,18],member:[0,17],menv_port:[],merg:18,messag:[7,13,17],meth:17,method:[0,6,7,8,13,17,18,20],mgr_cl:17,mid:15,midpoint:[15,16],might:[0,8,15,17],min:19,minimum:19,mirror:15,mod:1,mode:15,modifi:6,modul:[0,1,3,7,8,9,11,13,14,17,18,19],modulofeatur:10,more:[6,8,18],most:[7,18],msg:17,msgpack:17,much:17,multi:[],multienviron:[7,17,20],multienvmanag:[7,17],multipl:[],multiprocess:[],must:[0,3,5,7,17,20],myagent:[5,6],myagent_kwarg:6,myart:9,myartifact:[9,19],myenv:6,myfeat:9,myfeatur:9,myleaf2:19,myleaf:19,mymodul:6,myparam:9,myrul:19,mysteri:6,mytyp:9,n_agent:[6,20],name:[0,8,9,13,17,20],ndarrai:16,nearbi:18,need:[0,6,7,8,13,17],next:[6,18,20],node:[7,18],nodes_readi:7,non:[8,17],non_euclidian_angl:6,none:[0,3,7,8,9,17,19,20],noth:0,notimplementederror:[0,6,9],now:[],number:[0,1,6,8,17],numberag:1,numpi:16,obj:[3,13],object:[0,3,8,10,13,17],objectlogg:[8,13],observ:6,obtain:17,off:[8,17,18],offer:[6,19],older:17,omit:0,onc:[6,17,20],one:[8,17],onli:[0,8,13,17,19],oper:8,opinion:[0,18],opposit:0,option:[7,20],optional:[7,8],order:[7,8,17,18,19,20],ordere:0,origin:17,other:[0,7,8,9,17,18,19],otherwis:[0,7,17,19],output:18,outsid:17,over:[7,15,18],overal:[0,18],overrid:[0,6,7,8,9,17],overridden:[0,6,9],overwrit:20,own:[0,5,6,7,14,17,18],packag:[4,12],page:11,pair:[18,19],paramet:[0,3,5,6,7,8,9,13,14,15,16,17,18,19,20],parat:20,particular:[7,8,17],pass:[5,6,13,17,20],path:13,pdf:16,peopl:18,per:0,perform:[0,6,8,17],perform_vot:[8,17],pip:12,place:20,platform:18,pmax:15,point:[15,16],pool:[7,17],port:[7,17],possibl:[3,9,14,15,18,20],predefin:19,prefer:[15,18],prefix:13,prepar:[7,8,17],prepare_nod:7,present:7,previous:20,principl:18,probabl:[7,15,16],process:[7,17],processor:17,progress:20,project:[11,12],promin:0,propag:7,properti:7,provid:[8,18],proxi:[0,17],prune:[0,8,17],publish:[0,8,17],purpos:1,pval:15,python:12,pyvenv:12,qualifi:0,qualnam:0,quit:18,rais:[0,6,7,8,9,17],random:[0,8,17,20],random_addr:17,random_connect:0,rang:[6,7],rank:0,reachabl:17,readabl:0,readi:[7,8,17],readthedoc:12,reason:0,reduc:17,refil:0,rel:15,relev:17,remaind:10,remot:[],remov:[0,8,17],remove_connect:0,remove_rul:0,renam:17,repeatedli:17,report:17,repositori:[11,12],repres:[15,18],requir:[8,12,17],research:[11,18],resourc:[0,7],result:[1,7,17],ret:[9,18],rise:6,rogu:7,root:[8,13,17],rout:18,routin:8,rpc:[8,18],rtype:[0,9,14],rule:[],ruleleaf:19,ruleset:9,run:[4,7,8,17,18,20],run_until_complet:7,rype:[8,17],same:[7,8,17,20],sanit:0,sanitized_nam:0,save:[0,8,17],save_info:[8,17],score:8,search:[1,11],second:[7,15,17],section:18,see:[16,17,18],seealso:17,seem:17,seen:[0,18],select:[8,17],self:5,send:[7,17],serial:17,serializ:0,serv:[0,6,14,18],server:7,servic:8,set:[0,6,8,9,13,17,18,20],set_attitud:[0,18],set_host_addr:17,set_host_manag:17,set_se:17,set_weight:0,setproctitl:17,sever:[7,17,18],share:[0,18],shareabl:18,shelf:18,shift:15,shortcut:0,should:[0,5,7,8,9,17,19,20],show:0,shown:17,shuffl:20,shut:8,shutdown:17,sigmoid:[15,16],sim:6,similar:18,similarli:17,simul:[],singl:[0,6,14,17,18,20],singular:[8,17],size:17,slave:[7,17],slave_addr:17,slave_env_cl:17,slave_mgr_cl:17,slave_param:17,slight:6,smallest:17,social:0,societi:[0,8,17],some:[6,7,8,15,18,20],sort:[0,20],sourc:[0,1,3,6,7,8,9,10,12,13,14,15,16,17,19,20],space:18,span:7,spawn:[7,17],spawn_cmd:7,spawn_contain:17,spawn_n:17,spawn_nod:7,specifi:[8,17],ssh:7,ssh_exec:7,ssh_exec_in_new_loop:7,stand:18,standard:[14,15,16],starspawn:6,starspawnag:6,start:[8,12,17],state:8,std:[15,16],steep:[15,16],step:[0,6,20],stop:[7,17],stop_nod:7,stop_receiv:17,str:[0,7,8,9,13,16,17,20],straight:15,streamhandl:13,string:17,structur:19,subclass:[0,6,7,8,9,13,17,20],subfold:13,subject:[8,17],subrul:19,subset:0,successfulli:[0,17],sunken:6,support:[],system:[],take:[9,18,19,20],task:[7,17,18],tcp:[],test:[1,18],than:17,thei:[5,7,8,15,17,18],them:[1,7,15,17,18],therefor:18,thi:[0,6,7,8,9,13,14,15,17,18,19,20],thing:5,though:[7,14,18],thought:0,thu:17,time:[3,6,7,8,17,20],timeout:7,titl:17,todo:[6,19],togeth:18,toi:18,tool:[11,18],top:18,toward:[0,18],track:[],trait:0,transform:15,treelik:19,tri:9,trigger:[0,6,7,8,17,20],trigger_act:[8,17],trigger_al:[7,8,17],tupl:[0,7,17],turn:6,two:[15,19],txt:12,type:[0,8,9,13,14,15,16,17,19],typeerror:0,typic:17,unalt:17,unattend:7,underli:13,unexpect:7,unfinish:20,union:19,uniqu:[],unit:18,univers:8,unlimit:0,untest:17,until:7,unwant:0,usag:[7,13],usage:9,used:[8,17],user:[7,19],usual:[8,14,17],util:[8,13,16,17],valid:[0,8,17],validate_candid:[8,17],valu:[7,9,13,14,15,16,17,18,20],value_set:15,valueerror:8,variabl:[0,13],variou:[1,10,15,16],venv:12,veri:[0,17,18],veto:[8,17],virtual:12,virtualenv:12,vote:[0,8,17],wai:[6,12,17],wait:[7,17],wait_nod:7,want:[8,12,17],weather:6,weight:[0,18,19],weighted_averag:19,what:6,when:[7,8,9,10,17,19,20],where:[0,5,7,8,18,19,20],which:[0,3,6,7,8,17,18,19,20],who:3,whole:17,wikipedia:16,wind:6,wish:6,within:17,without:[7,17],won:18,work:[17,18],worst:[8,17],write:[13,19],written:13,yet:[7,18],you:[6,12,17],your:[5,6,7,12,18],yourself:18,zero:10},titles:["Agent","Agents","API Documentation","Artifact","Core","Implementing Agent Classes","Using Simulation","Distributed Systems","Environment","Feature","Features","Creamas - Creative Multi-Agent Systems","Installation","Logging","Mapper","Mappers","Math","Multiprocessing functionality","Overview","Rule","Simulation"],titleterms:{"class":5,"function":17,advanc:6,agent:[0,1,5,11,18],api:2,artifact:3,complex:6,core:[4,18],creama:11,creativ:11,develop:12,distribut:[7,18],document:2,environ:[8,18],featur:[9,10,18],implement:5,indice:11,install:12,installat:12,log:[6,13],mapper:[14,15,18],math:16,multi:11,multipl:18,multiprocess:17,overview:18,rule:[18,19],setup:6,simpl:6,simul:[6,18,20],support:18,system:[7,11,18],tabl:11,using:6,version:12}})